from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Commission,
    CommissionAdjustment,
    CommissionStatusEnum,
)
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

    model_config = ConfigDict(from_attributes=True)


@router.get("/commissions", response_model=List[CommissionSchema])
def list_commissions(
    status: Optional[CommissionStatusEnum] = None,
    partner_id: Optional[str] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        query = db.query(Commission)
        if status:
            query = query.filter(Commission.status == status)
        if partner_id:
            query = query.filter(Commission.partner_id == partner_id)
        if start:
            query = query.filter(Commission.created_at >= start)
        if end:
            query = query.filter(Commission.created_at <= end)
        records = query.order_by(Commission.created_at.desc()).all()
        return [CommissionSchema.model_validate(r, from_attributes=True) for r in records]


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
        record.status = CommissionStatusEnum.approved
        if form.note is not None:
            record.note = form.note
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
        record.status = CommissionStatusEnum.rejected
        if form.note is not None:
            record.note = form.note
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
        if not db.get(Commission, commission_id):
            raise HTTPException(status_code=404, detail="Commission not found")
        adj = CommissionAdjustment(
            commission_id=commission_id, amount=form.amount, reason=form.reason
        )
        db.add(adj)
        db.commit()
    return {"id": commission_id, "adjustment": str(form.amount)}
