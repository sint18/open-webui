import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_
from open_webui.internal.db import get_db
from open_webui.models.users import User
from open_webui.models.affiliate import PartnerProfile, PartnerStatusEnum
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class PartnerSchema(BaseModel):
    id: str
    name: str
    email: str
    role: str
    info: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/partners", response_model=List[PartnerSchema])
def search_partners(q: Optional[str] = None, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        query = db.query(User)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
        records = query.all()
        return [PartnerSchema.model_validate(r, from_attributes=True) for r in records]


class PartnerUpdateForm(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    rate_override: Optional[float] = None
    suspended: Optional[bool] = None
    terms_version: Optional[str] = None
    blocked_channels: Optional[List[str]] = None


@router.put("/partners/{partner_id}", response_model=PartnerSchema)
def update_partner(
    partner_id: str, form: PartnerUpdateForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        partner = db.get(User, partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        if form.name:
            partner.name = form.name
        if form.email:
            partner.email = form.email
        info = partner.info or {}
        if form.rate_override is not None:
            info["rate_override"] = form.rate_override
        if form.suspended is not None:
            info["suspended"] = form.suspended
        if form.blocked_channels is not None:
            info["blocked_channels"] = form.blocked_channels
        partner.info = info

        if form.terms_version is not None:
            profile = db.get(PartnerProfile, partner_id)
            if not profile:
                profile = PartnerProfile(partner_id=partner_id, status=PartnerStatusEnum.inactive)
                db.add(profile)
            profile.terms = {"version": form.terms_version, "accepted_at": int(time.time())}
            profile.updated_at = int(time.time())
        db.commit()
        db.refresh(partner)
        return PartnerSchema.model_validate(partner, from_attributes=True)


@router.post("/partners/{partner_id}/activate")
def activate_partner(partner_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        partner = db.get(User, partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        info = partner.info or {}
        info["suspended"] = False
        partner.info = info
        db.commit()
    return {"id": partner_id, "status": "active"}


@router.post("/partners/{partner_id}/suspend")
def suspend_partner(partner_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        partner = db.get(User, partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        info = partner.info or {}
        info["suspended"] = True
        partner.info = info
        db.commit()
    return {"id": partner_id, "status": "suspended"}
