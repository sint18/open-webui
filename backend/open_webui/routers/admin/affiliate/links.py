import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from open_webui.internal.db import get_db
from open_webui.models.affiliate import Link, AuditLog, AuditSeverityEnum
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class LinkSchema(BaseModel):
    id: str
    partner_id: str
    code: str
    url: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    active: bool
    created_at: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/links", response_model=List[LinkSchema])
def list_links(
    partner_id: Optional[str] = None,
    active: Optional[bool] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        query = db.query(Link)
        if partner_id:
            query = query.filter(Link.partner_id == partner_id)
        if active is not None:
            query = query.filter(Link.active == active)
        if start:
            query = query.filter(Link.created_at >= start)
        if end:
            query = query.filter(Link.created_at <= end)
        records = query.order_by(Link.created_at.desc()).all()
        return [LinkSchema.model_validate(r, from_attributes=True) for r in records]


class LinkCreateForm(BaseModel):
    partner_id: str
    code: str
    url: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    active: Optional[bool] = True


@router.post("/links", response_model=LinkSchema)
def create_link(form: LinkCreateForm, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        if db.query(Link).filter(Link.code == form.code).first():
            raise HTTPException(status_code=400, detail="Link code already exists")
        link = Link(
            partner_id=form.partner_id,
            code=form.code,
            url=form.url,
            utm_source=form.utm_source,
            utm_medium=form.utm_medium,
            utm_campaign=form.utm_campaign,
            utm_term=form.utm_term,
            utm_content=form.utm_content,
            active=form.active if form.active is not None else True,
            created_at=int(time.time()),
        )
        db.add(link)
        db.add(
            AuditLog(
                partner_id=form.partner_id,
                action="create_link",
                severity=AuditSeverityEnum.info,
                details={"link_id": link.id},
            )
        )
        db.commit()
        db.refresh(link)
        return LinkSchema.model_validate(link, from_attributes=True)


class LinkUpdateForm(BaseModel):
    code: Optional[str] = None
    url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    active: Optional[bool] = None


@router.patch("/links/{link_id}", response_model=LinkSchema)
def update_link(link_id: str, form: LinkUpdateForm, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        link = db.get(Link, link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        if form.code and form.code != link.code:
            if db.query(Link).filter(Link.code == form.code).first():
                raise HTTPException(status_code=400, detail="Link code already exists")
            link.code = form.code
        for field in [
            "url",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "active",
        ]:
            value = getattr(form, field)
            if value is not None:
                setattr(link, field, value)
        db.add(
            AuditLog(
                partner_id=link.partner_id,
                action="update_link",
                severity=AuditSeverityEnum.info,
                details={"link_id": link.id, "changes": form.model_dump(exclude_none=True)},
            )
        )
        db.commit()
        db.refresh(link)
        return LinkSchema.model_validate(link, from_attributes=True)


@router.delete("/links/{link_id}")
def delete_link(link_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        link = db.get(Link, link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        db.delete(link)
        db.add(
            AuditLog(
                partner_id=link.partner_id,
                action="delete_link",
                severity=AuditSeverityEnum.warning,
                details={"link_id": link_id},
            )
        )
        db.commit()
    return {"id": link_id, "deleted": True}
