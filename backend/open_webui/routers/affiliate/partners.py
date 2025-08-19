from decimal import Decimal
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from open_webui.core.affiliate.crypto import encrypt_details, decrypt_details
from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Application,
    ApplicationStatusEnum,
    Link,
    Coupon,
    Commission,
    CommissionAdjustment,
    CommissionTypeEnum,
    CommissionStatusEnum,
    PartnerProfile,
    PartnerStatusEnum,
    PartnerTypeEnum,
    AuditLog,
    AuditSeverityEnum,
)
from open_webui.models.discount import DiscountCode
from open_webui.utils.auth import get_verified_user

router = APIRouter()


class PartnerProfileSchema(BaseModel):
    partner_id: str
    website: str | None = None
    status: PartnerStatusEnum
    type: PartnerTypeEnum
    payout_method: str | None = None
    payout_details: dict | None = None
    terms: dict | None = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


def to_profile_schema(profile: PartnerProfile) -> PartnerProfileSchema:
    return PartnerProfileSchema(
        partner_id=profile.partner_id,
        website=profile.website,
        status=profile.status,
        type=profile.type,
        payout_method=profile.payout_method,
        payout_details=
            decrypt_details(profile.payout_details) if profile.payout_details else None,
        terms=profile.terms,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


class PartnerMeResponse(BaseModel):
    id: str
    total_commission: Decimal = Decimal("0")
    profile: PartnerProfileSchema | None = None


@router.get("/partners/me", response_model=PartnerMeResponse)
def get_partner_me(user=Depends(get_verified_user)):
    """Return basic partner information and totals."""
    total = Decimal("0")
    with get_db() as db:
        result = db.execute(
            text(
                "SELECT total_amount FROM affiliate.partner_commission_totals WHERE partner_id=:pid"
            ),
            {"pid": user.id},
        ).scalar()
        profile = db.get(PartnerProfile, user.id)
    if result:
        total = Decimal(result)
    profile_schema = to_profile_schema(profile) if profile else None
    return PartnerMeResponse(id=user.id, total_commission=total, profile=profile_schema)


class TermsAcceptanceForm(BaseModel):
    version: str


@router.post("/partners/me/accept-terms")
def accept_terms(form: TermsAcceptanceForm, user=Depends(get_verified_user)):
    with get_db() as db:
        profile = db.get(PartnerProfile, user.id)
        if not profile:
            profile = PartnerProfile(partner_id=user.id, status=PartnerStatusEnum.inactive)
            db.add(profile)
        profile.terms = {"version": form.version, "accepted_at": int(time.time())}
        profile.updated_at = int(time.time())
        db.commit()
    return {"status": "accepted", "version": form.version}


@router.post("/partners/apply")
def apply_for_affiliate(user=Depends(get_verified_user)):
    with get_db() as db:
        existing = (
            db.query(Application)
            .filter(Application.partner_id == user.id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Application already exists")
        profile = db.get(PartnerProfile, user.id)
        if not profile:
            profile = PartnerProfile(partner_id=user.id, status=PartnerStatusEnum.inactive)
            db.add(profile)
        else:
            profile.status = PartnerStatusEnum.inactive
            profile.updated_at = int(time.time())
        application = Application(partner_id=user.id, status=ApplicationStatusEnum.pending)
        db.add(application)
        db.commit()
        return {"id": application.id, "status": application.status}


class PartnerProfileUpdate(BaseModel):
    website: str | None = None
    status: PartnerStatusEnum | None = None
    type: PartnerTypeEnum | None = None


@router.put("/partners/me/profile", response_model=PartnerProfileSchema)
def update_profile(form: PartnerProfileUpdate, user=Depends(get_verified_user)):
    with get_db() as db:
        profile = db.get(PartnerProfile, user.id)
        if not profile:
            profile = PartnerProfile(partner_id=user.id)
            db.add(profile)
        if form.website is not None:
            profile.website = form.website
        if form.status is not None:
            profile.status = form.status
        if form.type is not None:
            profile.type = form.type
        profile.updated_at = int(time.time())
        db.add(
            AuditLog(
                partner_id=user.id,
                action="update_profile",
                severity=AuditSeverityEnum.info,
                details={"website": form.website},
            )
        )
        db.commit()
        db.refresh(profile)
        return to_profile_schema(profile)


class PayoutInfo(BaseModel):
    method: str | None = None
    details: dict | None = None


@router.get("/partners/me/payout-info", response_model=PayoutInfo)
def get_payout_info(user=Depends(get_verified_user)):
    with get_db() as db:
        profile = db.get(PartnerProfile, user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Partner profile not found")
        details = decrypt_details(profile.payout_details) if profile.payout_details else None
        return PayoutInfo(method=profile.payout_method, details=details)


@router.put("/partners/me/payout-info", response_model=PayoutInfo)
def update_payout_info(form: PayoutInfo, user=Depends(get_verified_user)):
    with get_db() as db:
        profile = db.get(PartnerProfile, user.id)
        if not profile:
            profile = PartnerProfile(partner_id=user.id, status=PartnerStatusEnum.inactive)
            db.add(profile)
        if form.method is not None:
            profile.payout_method = form.method
        if form.details is not None:
            profile.payout_details = encrypt_details(form.details)
        profile.updated_at = int(time.time())
        db.add(
            AuditLog(
                partner_id=user.id,
                action="update_payout_info",
                severity=AuditSeverityEnum.info,
                details={"method": form.method},
            )
        )
        db.commit()
        db.refresh(profile)
        details = decrypt_details(profile.payout_details) if profile.payout_details else None
        return PayoutInfo(method=profile.payout_method, details=details)


class LinkBase(BaseModel):
    code: str
    url: str


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    code: str | None = None
    url: str | None = None


class LinkSchema(LinkBase):
    id: str
    created_at: int

    model_config = ConfigDict(from_attributes=True)


@router.post("/partners/me/links", response_model=LinkSchema)
def create_link(form: LinkCreate, user=Depends(get_verified_user)):
    with get_db() as db:
        if db.query(Link).filter(Link.code == form.code).first():
            raise HTTPException(status_code=400, detail="Code already exists")
        record = Link(partner_id=user.id, code=form.code, url=form.url)
        db.add(record)
        db.add(
            AuditLog(
                partner_id=user.id,
                action="create_link",
                severity=AuditSeverityEnum.info,
                details={"link_id": record.id},
            )
        )
        db.commit()
        db.refresh(record)
        return LinkSchema.model_validate(record, from_attributes=True)


@router.get("/partners/me/links", response_model=List[LinkSchema])
def list_links(user=Depends(get_verified_user)):
    with get_db() as db:
        records = (
            db.query(Link)
            .filter(Link.partner_id == user.id)
            .order_by(Link.created_at.desc())
            .all()
        )
        return [LinkSchema.model_validate(r, from_attributes=True) for r in records]


@router.put("/partners/me/links/{link_id}", response_model=LinkSchema)
def update_link(link_id: str, form: LinkUpdate, user=Depends(get_verified_user)):
    with get_db() as db:
        record = (
            db.query(Link)
            .filter(Link.id == link_id, Link.partner_id == user.id)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Link not found")
        if form.code and form.code != record.code:
            if db.query(Link).filter(Link.code == form.code).first():
                raise HTTPException(status_code=400, detail="Code already exists")
            record.code = form.code
        if form.url:
            record.url = form.url
        db.commit()
        db.refresh(record)
        return LinkSchema.model_validate(record, from_attributes=True)


@router.delete("/partners/me/links/{link_id}")
def delete_link(link_id: str, user=Depends(get_verified_user)):
    with get_db() as db:
        record = (
            db.query(Link)
            .filter(Link.id == link_id, Link.partner_id == user.id)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Link not found")
        db.delete(record)
        db.add(
            AuditLog(
                partner_id=user.id,
                action="delete_link",
                severity=AuditSeverityEnum.warning,
                details={"link_id": link_id},
            )
        )
        db.commit()
    return {"status": "deleted"}


class CouponSchema(BaseModel):
    id: str
    code: str
    discount_percent: Decimal | None = None
    expires_at: int | None = None
    active: bool
    created_at: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/partners/me/coupons", response_model=List[CouponSchema])
def list_coupons(user=Depends(get_verified_user)):
    with get_db() as db:
        records = (
            db.query(Coupon, DiscountCode)
            .join(DiscountCode, Coupon.code == DiscountCode.code)
            .filter(Coupon.partner_id == user.id)
            .order_by(Coupon.created_at.desc())
            .all()
        )
        results: List[CouponSchema] = []
        for c, d in records:
            results.append(
                CouponSchema(
                    id=c.id,
                    code=d.code,
                    discount_percent=Decimal(d.discount_percent) if d.discount_percent is not None else None,
                    expires_at=c.expires_at or d.expires_at,
                    active=c.active and d.active,
                    created_at=c.created_at,
                )
            )
        return results




class AdjustmentSchema(BaseModel):
    id: str
    amount: Decimal
    reason: str | None = None
    created_at: int

    model_config = ConfigDict(from_attributes=True)


class LedgerEntry(BaseModel):
    id: str
    order_id: str
    type: CommissionTypeEnum
    status: CommissionStatusEnum
    amount: Decimal
    created_at: int
    adjustments: List[AdjustmentSchema] = []
    note: str | None = None


@router.get("/partners/me/ledger", response_model=List[LedgerEntry])
def get_ledger(user=Depends(get_verified_user)):
    with get_db() as db:
        commissions = (
            db.query(Commission)
            .filter(Commission.partner_id == user.id)
            .order_by(Commission.created_at.desc())
            .all()
        )
        results: List[LedgerEntry] = []
        for c in commissions:
            adjustments = (
                db.query(CommissionAdjustment)
                .filter(CommissionAdjustment.commission_id == c.id)
                .all()
            )
            results.append(
                LedgerEntry(
                    id=c.id,
                    order_id=c.order_id,
                    type=c.type,
                    status=c.status,
                    amount=c.amount,
                    created_at=c.created_at,
                    note=c.note,
                    adjustments=[
                        AdjustmentSchema.model_validate(a, from_attributes=True)
                        for a in adjustments
                    ],
                )
            )
        return results
