from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    DiscountCodeBinding,
    AuditLog,
    AuditSeverityEnum,
)
from open_webui.models.discount import DiscountCode
from open_webui.utils.auth import get_admin_or_support_user


router = APIRouter()


class DiscountCodeBindingSchema(BaseModel):
    id: str
    partner_id: str
    code: str
    discount_percent: Decimal | None = None
    expires_at: int | None = None
    active: bool
    created_at: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/coupons", response_model=List[DiscountCodeBindingSchema])
def list_coupons(
    partner_id: Optional[str] = None, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        query = (
            db.query(DiscountCodeBinding, DiscountCode)
            .join(DiscountCode, DiscountCodeBinding.code == DiscountCode.code)
        )
        if partner_id:
            query = query.filter(DiscountCodeBinding.partner_id == partner_id)
        records = query.order_by(DiscountCodeBinding.created_at.desc()).all()
        results: List[DiscountCodeBindingSchema] = []
        for c, d in records:
            results.append(
                DiscountCodeBindingSchema(
                    id=c.id,
                    partner_id=c.partner_id,
                    code=d.code,
                    discount_percent=Decimal(d.discount_percent)
                    if d.discount_percent is not None
                    else None,
                    expires_at=c.expires_at or d.expires_at,
                    active=c.active and d.active,
                    created_at=c.created_at,
                )
            )
        return results


class DiscountCodeBindingAttachForm(BaseModel):
    partner_id: str
    code: str
    discount_percent: Optional[int] = None
    expires_at: Optional[int] = None
    active: bool = True


@router.post("/coupons/attach")
def attach_coupon(
    form: DiscountCodeBindingAttachForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        if (
            db.query(DiscountCodeBinding)
            .filter(DiscountCodeBinding.code == form.code)
            .first()
        ):
            raise HTTPException(status_code=400, detail="Discount code already attached")

        discount = db.query(DiscountCode).filter(DiscountCode.code == form.code).first()
        if not discount:
            discount = DiscountCode(
                code=form.code,
                discount_percent=form.discount_percent,
                expires_at=form.expires_at,
                active=form.active,
            )
            db.add(discount)

        binding = DiscountCodeBinding(
            partner_id=form.partner_id,
            code=form.code,
            expires_at=form.expires_at,
            active=form.active,
        )
        db.add(binding)
        db.add(
            AuditLog(
                partner_id=form.partner_id,
                action="attach_coupon",
                severity=AuditSeverityEnum.info,
                details={"coupon_id": binding.id, "code": form.code},
            )
        )
        db.commit()
        return {"id": binding.id, "status": "attached"}


@router.post("/coupons/{coupon_id}/detach")
def detach_coupon(coupon_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        record = db.get(DiscountCodeBinding, coupon_id)
        if not record:
            raise HTTPException(status_code=404, detail="Discount code binding not found")
        partner_id = record.partner_id
        db.delete(record)
        db.add(
            AuditLog(
                partner_id=partner_id,
                action="detach_coupon",
                severity=AuditSeverityEnum.warning,
                details={"coupon_id": coupon_id},
            )
        )
        db.commit()
        return {"id": coupon_id, "status": "detached"}


class DiscountCodeBindingUpdateForm(BaseModel):
    code: Optional[str] = None
    discount_percent: Optional[int] = None
    expires_at: Optional[int] = None
    active: Optional[bool] = None


@router.put("/coupons/{coupon_id}")
def update_coupon(
    coupon_id: str,
    form: DiscountCodeBindingUpdateForm,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        record = (
            db.query(DiscountCodeBinding, DiscountCode)
            .join(DiscountCode, DiscountCodeBinding.code == DiscountCode.code)
            .filter(DiscountCodeBinding.id == coupon_id)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Discount code binding not found")
        binding, discount = record

        changes = {}

        if form.code and form.code != binding.code:
            if db.query(DiscountCode).filter(DiscountCode.code == form.code).first():
                raise HTTPException(status_code=400, detail="Discount code already exists")
            discount.code = form.code
            binding.code = form.code
            changes["code"] = form.code

        if form.discount_percent is not None:
            discount.discount_percent = form.discount_percent
            changes["discount_percent"] = form.discount_percent

        if form.expires_at is not None:
            binding.expires_at = form.expires_at
            discount.expires_at = form.expires_at
            changes["expires_at"] = form.expires_at

        if form.active is not None:
            binding.active = form.active
            discount.active = form.active
            changes["active"] = form.active

        if changes:
            db.add(
                AuditLog(
                    partner_id=binding.partner_id,
                    action="update_coupon",
                    severity=AuditSeverityEnum.info,
                    details={"coupon_id": coupon_id, **changes},
                )
            )
        db.commit()
        return {"id": coupon_id, "status": "updated"}

