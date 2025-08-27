from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Commission,
    CommissionAdjustment,
    CommissionStatusEnum,
    CommissionTypeEnum,
    FraudFlag,
)
from open_webui.models.audit import AuditLog
from open_webui.models.billing import PaymentOrder
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


class CommissionSchema(BaseModel):
    id: str
    partner_id: str
    order_id: str
    type: str
    status: CommissionStatusEnum
    amount: Decimal
    created_at: int
    note: str | None = None
    fraud_flags: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class TotalsFooter(BaseModel):
    total_amount: Decimal


class CommissionListResponse(BaseModel):
    items: List[CommissionSchema]
    footer: TotalsFooter


@router.get("/commissions", response_model=CommissionListResponse)
def list_commissions(
    status: Optional[CommissionStatusEnum] = None,
    type: Optional[CommissionTypeEnum] = None,
    partner_id: Optional[str] = None,
    order_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    flagged: bool = False,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        query = db.query(Commission)
        if status:
            query = query.filter(Commission.status == status)
        if type:
            query = query.filter(Commission.type == type)
        if partner_id:
            query = query.filter(Commission.partner_id == partner_id)
        if order_id:
            query = query.filter(Commission.order_id == order_id)
        if plan_id:
            query = query.join(PaymentOrder, PaymentOrder.order_id == Commission.order_id)
            query = query.filter(PaymentOrder.plan_id == plan_id)
        if start:
            query = query.filter(Commission.created_at >= start)
        if end:
            query = query.filter(Commission.created_at <= end)
        records = query.order_by(Commission.created_at.desc()).all()
        results: List[CommissionSchema] = []
        total_amount = Decimal("0")
        for r in records:
            flags = [
                f.flag_type
                for f in db.query(FraudFlag).filter(FraudFlag.partner_id == r.partner_id)
            ]
            if flagged and not flags:
                continue
            comm = CommissionSchema.model_validate(r, from_attributes=True)
            comm.fraud_flags = flags
            results.append(comm)
            total_amount += Decimal(r.amount)
        return CommissionListResponse(
            items=results, footer=TotalsFooter(total_amount=total_amount)
        )


class ActionForm(BaseModel):
    note: str | None = None


@router.post("/commissions/{commission_id}/approve")
def approve_commission(
    commission_id: str, form: ActionForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        record = db.get(Commission, commission_id)
        if not record:
            raise HTTPException(status_code=404, detail="Commission not found")
        before = {"status": record.status.value, "note": record.note}
        if record.status == CommissionStatusEnum.approved:
            return {"id": commission_id, "status": "approved"}

        previous_status = record.status
        record.status = CommissionStatusEnum.approved
        if form.note is not None:
            record.note = form.note
        after = {"status": record.status.value, "note": record.note}
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"commission:{commission_id}",
                action="approve_commission",
                before=before,
                after=after,
                reason=form.note,
            )
        )
        db.commit()
    return {"id": commission_id, "status": "approved"}


@router.post("/commissions/{commission_id}/void")
def void_commission(
    commission_id: str, form: ActionForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        record = db.get(Commission, commission_id)
        if not record:
            raise HTTPException(status_code=404, detail="Commission not found")
        if record.status == CommissionStatusEnum.rejected:
            return {"id": commission_id, "status": "void"}

        previous_status = record.status
        before = {"status": record.status.value, "note": record.note}
        record.status = CommissionStatusEnum.rejected
        if form.note is not None:
            record.note = form.note
        after = {"status": record.status.value, "note": record.note}
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"commission:{commission_id}",
                action="void_commission",
                before=before,
                after=after,
                reason=form.note,
            )
        )
        db.commit()
    return {"id": commission_id, "status": "void"}


class AdjustmentForm(BaseModel):
    amount: Decimal
    reason: Optional[str] = None


@router.post("/commissions/{commission_id}/adjust")
def adjust_commission(
    commission_id: str, form: AdjustmentForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        record = db.get(Commission, commission_id)
        if not record:
            raise HTTPException(status_code=404, detail="Commission not found")
        existing = (
            db.query(CommissionAdjustment)
            .filter(
                CommissionAdjustment.commission_id == commission_id,
                CommissionAdjustment.amount == form.amount,
                CommissionAdjustment.reason == form.reason,
            )
            .first()
        )
        if existing:
            return {"id": commission_id, "adjustment": str(existing.amount)}

        adj = CommissionAdjustment(
            commission_id=commission_id, amount=form.amount, reason=form.reason
        )
        db.add(adj)
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"commission:{commission_id}",
                action="adjust_commission",
                before=None,
                after={
                    "adjustment_id": adj.id,
                    "amount": str(form.amount),
                    "reason": form.reason,
                },
                reason=form.reason,
            )
        )
        db.commit()
    return {"id": commission_id, "adjustment": str(form.amount)}


@router.post("/commissions/{commission_id}/flags/review")
def review_commission_flags(
    commission_id: str, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        record = db.get(Commission, commission_id)
        if not record:
            raise HTTPException(status_code=404, detail="Commission not found")
        flags = [
            f.flag_type
            for f in db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id)
        ]
        db.query(FraudFlag).filter(FraudFlag.partner_id == record.partner_id).delete()
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"commission:{commission_id}",
                action="review_commission_flags",
                before={"flags": flags},
                after={"flags": []},
                reason=None,
            )
        )
        db.commit()
    return {"id": commission_id, "flags_cleared": True}
