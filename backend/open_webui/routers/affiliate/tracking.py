import datetime
import hashlib

from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel

from open_webui.env import WEBUI_AUTH_COOKIE_SAME_SITE, WEBUI_AUTH_COOKIE_SECURE
from open_webui.internal.db import get_db
from open_webui.models.affiliate import Click, Attribution, AttrViaEnum

router = APIRouter()


class ClickForm(BaseModel):
    partner_id: str
    link_id: str | None = None
    coupon_id: str | None = None


@router.post("/click")
async def track_click(form: ClickForm, request: Request, response: Response):
    """Track an affiliate click and set identification cookies."""
    user_agent = request.headers.get("User-Agent", "")
    dedupe_hash = hashlib.sha256(
        f"{form.partner_id}:{form.link_id or ''}:{form.coupon_id or ''}:{user_agent}".encode()
    ).hexdigest()

    # If the dedupe hash matches the cookie, avoid duplicate insert
    if request.cookies.get("aff_click_hash") == dedupe_hash:
        existing_id = request.cookies.get("aff_click_id")
        if existing_id:
            return {"click_id": existing_id}

    with get_db() as db:
        record = Click(
            partner_id=form.partner_id,
            link_id=form.link_id,
            coupon_id=form.coupon_id,
            user_agent=user_agent,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    response.set_cookie(
        key="aff_click_id",
        value=str(record.id),
        expires=expires,
        httponly=True,
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
    )
    response.set_cookie(
        key="aff_click_hash",
        value=dedupe_hash,
        expires=expires,
        httponly=True,
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
    )

    return {"click_id": record.id}


class AttributionForm(BaseModel):
    partner_id: str
    attr_via: AttrViaEnum
    click_id: int | None = None
    email: str | None = None


@router.post("/attribution")
async def create_attribution(
    form: AttributionForm, request: Request, response: Response
):
    """Create an attribution record based on a tracked click."""
    click_id = form.click_id or request.cookies.get("aff_click_id")
    if not click_id:
        raise HTTPException(status_code=400, detail="click_id missing")

    email_hash = None
    if form.email:
        email_hash = hashlib.sha256(form.email.lower().encode()).hexdigest()

    dedupe_hash = hashlib.sha256(
        f"{form.partner_id}:{form.attr_via.value}:{click_id}:{email_hash or ''}".encode()
    ).hexdigest()

    if request.cookies.get("aff_attr_hash") == dedupe_hash:
        existing = request.cookies.get("aff_attr_id")
        if existing:
            return {"attribution_id": existing}

    with get_db() as db:
        record = Attribution(
            click_id=int(click_id), partner_id=form.partner_id, attr_via=form.attr_via
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    response.set_cookie(
        key="aff_attr_id",
        value=str(record.id),
        expires=expires,
        httponly=True,
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
    )
    response.set_cookie(
        key="aff_attr_hash",
        value=dedupe_hash,
        expires=expires,
        httponly=True,
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
    )
    if email_hash:
        response.set_cookie(
            key="aff_email_hash",
            value=email_hash,
            expires=expires,
            httponly=True,
            samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
            secure=WEBUI_AUTH_COOKIE_SECURE,
        )

    return {"attribution_id": record.id}
