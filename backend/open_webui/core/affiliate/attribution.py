import datetime
import hashlib
from typing import Optional

from fastapi import Request, Response

from open_webui.config import CONFIG_DATA
from open_webui.env import WEBUI_AUTH_COOKIE_SAME_SITE, WEBUI_AUTH_COOKIE_SECURE
from open_webui.models.affiliate import Attribution


def resolve_attribution_on_auth(email: str, request: Request, response: Response) -> None:
    """On authentication, renew attribution-related cookies and store email hash."""
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
    window = CONFIG_DATA.get("affiliate", {}).get("cookie_window_days", 30)
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=window)

    attr_id = request.cookies.get("aff_attr_id")
    if attr_id:
        response.set_cookie(
            key="aff_attr_id",
            value=attr_id,
            expires=expires,
            httponly=True,
            samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
            secure=WEBUI_AUTH_COOKIE_SECURE,
        )

    response.set_cookie(
        key="aff_email_hash",
        value=email_hash,
        expires=expires,
        httponly=True,
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
    )


def choose_final_attribution(
    coupon: Optional[Attribution] = None,
    last_click: Optional[Attribution] = None,
    manual: Optional[Attribution] = None,
) -> Optional[Attribution]:
    """Determine final attribution priority: coupon > last-click > manual."""
    model = CONFIG_DATA.get("affiliate", {}).get("attribution_model", "last_click")
    if model == "first_click":
        return coupon or manual or last_click
    return coupon or last_click or manual
