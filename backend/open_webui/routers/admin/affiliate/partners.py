import time
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_, text

from open_webui.core.affiliate.crypto import encrypt_details, decrypt_details
from open_webui.internal.db import get_db
from open_webui.models.users import User
from open_webui.models.affiliate import (
    PartnerProfile,
    PartnerStatusEnum,
)
from open_webui.models.audit import AuditLog
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class PartnerSchema(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: PartnerStatusEnum | None = None
    balance: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


class AuditLogSchema(BaseModel):
    id: str
    actor_id: str
    resource: str
    action: str
    before: dict | None = None
    after: dict | None = None
    reason: str | None = None
    timestamp: int

    model_config = ConfigDict(from_attributes=True)


class PartnerDetailSchema(PartnerSchema):
    payout_method: str | None = None
    payout_details: dict | None = None
    rates: dict | None = None
    audit_logs: List[AuditLogSchema] = []


@router.get("/partners", response_model=List[PartnerSchema])
def search_partners(q: Optional[str] = None, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        query = db.query(User, PartnerProfile).outerjoin(
            PartnerProfile, PartnerProfile.partner_id == User.id
        )
        if q:
            like = f"%{q}%"
            query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
        records = query.all()
        results: List[PartnerSchema] = []
        for user, profile in records:
            bal = db.execute(
                text(
                    "SELECT total_amount FROM affiliate.partner_commission_totals WHERE partner_id=:pid"
                ),
                {"pid": user.id},
            ).scalar()
            balance = Decimal(str(bal)) if bal is not None else Decimal("0")
            results.append(
                PartnerSchema(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    status=profile.status if profile else None,
                    balance=balance,
                )
            )
        return results


@router.get("/partners/{partner_id}", response_model=PartnerDetailSchema)
def get_partner(partner_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        user = db.get(User, partner_id)
        if not user:
            raise HTTPException(status_code=404, detail="Partner not found")
        profile = db.get(PartnerProfile, partner_id)
        bal = db.execute(
            text(
                "SELECT total_amount FROM affiliate.partner_commission_totals WHERE partner_id=:pid"
            ),
            {"pid": partner_id},
        ).scalar()
        balance = Decimal(str(bal)) if bal is not None else Decimal("0")
        details = (
            decrypt_details(profile.payout_details) if profile and profile.payout_details else None
        )
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.resource == f"partner:{partner_id}")
            .order_by(AuditLog.timestamp.desc())
            .limit(20)
            .all()
        )
        return PartnerDetailSchema(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            status=profile.status if profile else None,
            payout_method=profile.payout_method if profile else None,
            payout_details=details,
            rates=profile.rates if profile else None,
            balance=balance,
            audit_logs=[AuditLogSchema.model_validate(l, from_attributes=True) for l in logs],
        )


class PartnerUpdateForm(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[PartnerStatusEnum] = None
    payout_method: Optional[str] = None
    payout_details: Optional[dict] = None
    rates: Optional[dict] = None
    terms_version: Optional[str] = None
    blocked_channels: Optional[List[str]] = None


@router.put("/partners/{partner_id}", response_model=PartnerDetailSchema)
def update_partner(
    partner_id: str, form: PartnerUpdateForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        user = db.get(User, partner_id)
        if not user:
            raise HTTPException(status_code=404, detail="Partner not found")
        profile = db.get(PartnerProfile, partner_id)
        if not profile:
            profile = PartnerProfile(partner_id=partner_id, status=PartnerStatusEnum.inactive)
            db.add(profile)

        changes: dict = {}
        before: dict = {}

        if form.name:
            before["name"] = user.name
            user.name = form.name
            changes["name"] = form.name
        if form.email:
            before["email"] = user.email
            user.email = form.email
            changes["email"] = form.email
        if form.status is not None:
            before["status"] = profile.status.value
            profile.status = form.status
            changes["status"] = form.status.value
        if form.payout_method is not None:
            before["payout_method"] = profile.payout_method
            profile.payout_method = form.payout_method
            changes["payout_method"] = form.payout_method
        if form.payout_details is not None:
            profile.payout_details = encrypt_details(form.payout_details)
        if form.rates is not None:
            if admin.role != "admin":
                raise HTTPException(status_code=401, detail="Only admin can edit rates")
            before["rates"] = profile.rates
            profile.rates = form.rates
            changes["rates"] = form.rates
        if form.blocked_channels is not None:
            info = user.info or {}
            before["blocked_channels"] = info.get("blocked_channels")
            info["blocked_channels"] = form.blocked_channels
            user.info = info
            changes["blocked_channels"] = form.blocked_channels
        if form.terms_version is not None:
            before["terms_version"] = profile.terms.get("version") if profile.terms else None
            profile.terms = {
                "version": form.terms_version,
                "accepted_at": int(time.time()),
            }
            changes["terms_version"] = form.terms_version

        profile.updated_at = int(time.time())

        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"partner:{partner_id}",
                action="admin_update_partner",
                before=before,
                after=changes,
                reason=None,
            )
        )

        db.commit()
        db.refresh(user)
        db.refresh(profile)

        bal = db.execute(
            text(
                "SELECT total_amount FROM affiliate.partner_commission_totals WHERE partner_id=:pid"
            ),
            {"pid": partner_id},
        ).scalar()
        balance = Decimal(str(bal)) if bal is not None else Decimal("0")
        details = (
            decrypt_details(profile.payout_details) if profile.payout_details else None
        )
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.resource == f"partner:{partner_id}")
            .order_by(AuditLog.timestamp.desc())
            .limit(20)
            .all()
        )
        return PartnerDetailSchema(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            status=profile.status,
            payout_method=profile.payout_method,
            payout_details=details,
            rates=profile.rates,
            balance=balance,
            audit_logs=[AuditLogSchema.model_validate(l, from_attributes=True) for l in logs],
        )


@router.post("/partners/{partner_id}/activate")
def activate_partner(partner_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        profile = db.get(PartnerProfile, partner_id)
        before = {"status": profile.status.value} if profile else {"status": None}
        if not profile:
            profile = PartnerProfile(partner_id=partner_id, status=PartnerStatusEnum.active)
            db.add(profile)
        else:
            profile.status = PartnerStatusEnum.active
            profile.updated_at = int(time.time())
        after = {"status": profile.status.value}
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"partner:{partner_id}",
                action="admin_activate_partner",
                before=before,
                after=after,
                reason=None,
            )
        )
        db.commit()
    return {"id": partner_id, "status": "active"}


@router.post("/partners/{partner_id}/suspend")
def suspend_partner(partner_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        profile = db.get(PartnerProfile, partner_id)
        before = {"status": profile.status.value} if profile else {"status": None}
        if not profile:
            profile = PartnerProfile(partner_id=partner_id, status=PartnerStatusEnum.suspended)
            db.add(profile)
        else:
            profile.status = PartnerStatusEnum.suspended
            profile.updated_at = int(time.time())
        after = {"status": profile.status.value}
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"partner:{partner_id}",
                action="admin_suspend_partner",
                before=before,
                after=after,
                reason=None,
            )
        )
        db.commit()
    return {"id": partner_id, "status": "suspended"}
