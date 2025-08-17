from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Link,
    Coupon,
    Commission,
    CommissionAdjustment,
    CommissionTypeEnum,
    CommissionStatusEnum,
)
from open_webui.utils.auth import get_verified_user

router = APIRouter()


class PartnerMeResponse(BaseModel):
    id: str
    total_commission: Decimal = Decimal("0")


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
        if result:
            total = Decimal(result)
    return PartnerMeResponse(id=user.id, total_commission=total)


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
        db.commit()
    return {"status": "deleted"}


class CouponSchema(BaseModel):
    id: str
    code: str
    discount_percent: Decimal | None = None
    active: bool
    created_at: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/partners/me/coupons", response_model=List[CouponSchema])
def list_coupons(user=Depends(get_verified_user)):
    with get_db() as db:
        records = (
            db.query(Coupon)
            .filter(Coupon.partner_id == user.id)
            .order_by(Coupon.created_at.desc())
            .all()
        )
        return [CouponSchema.model_validate(r, from_attributes=True) for r in records]


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
