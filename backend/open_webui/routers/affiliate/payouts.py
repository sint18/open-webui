from decimal import Decimal
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from open_webui.config import CONFIG_DATA
from open_webui.core.affiliate.crypto import decrypt_details
from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Commission,
    CommissionStatusEnum,
    Payout,
    PayoutItem,
    PayoutStatusEnum,
    PartnerProfile,
)
from open_webui.utils.auth import get_verified_user

router = APIRouter()


class PayoutCreateForm(BaseModel):
    amount: Decimal
    fee_mmk: Decimal | None = None


@router.post("/payouts")
def create_payout(form: PayoutCreateForm, user=Depends(get_verified_user)):
    min_payout = Decimal(
        CONFIG_DATA.get("affiliate", {}).get("min_payout_amount", 0)
    )
    with get_db() as db:
        open_payout = (
            db.query(Payout)
            .filter(
                Payout.partner_id == user.id,
                Payout.status.in_(
                    [PayoutStatusEnum.pending, PayoutStatusEnum.approved]
                ),
            )
            .first()
        )
        if open_payout:
            raise HTTPException(status_code=400, detail="Existing payout request in progress")

        commissions = (
            db.query(Commission)
            .outerjoin(PayoutItem, PayoutItem.commission_id == Commission.id)
            .filter(
                Commission.partner_id == user.id,
                Commission.status == CommissionStatusEnum.approved,
                PayoutItem.id.is_(None),
            )
            .order_by(Commission.created_at.asc())
            .all()
        )
        eligible_balance = sum(Decimal(c.amount) for c in commissions)
        if eligible_balance < min_payout:
            raise HTTPException(status_code=400, detail="Eligible balance below minimum threshold")

        requested = Decimal(form.amount)
        if requested < min_payout:
            raise HTTPException(
                status_code=400,
                detail=f"Requested amount must be at least {min_payout}",
            )
        if requested > eligible_balance:
            raise HTTPException(
                status_code=400,
                detail="Requested amount exceeds eligible balance",
            )

        selected: List[Commission] = []
        total = Decimal("0")
        for commission in commissions:
            amt = Decimal(commission.amount)
            if total + amt > requested:
                break
            selected.append(commission)
            total += amt

        if not selected:
            raise HTTPException(status_code=400, detail="No commissions selected for payout")

        profile = db.get(PartnerProfile, user.id)
        if not profile or not profile.payout_details:
            raise HTTPException(status_code=400, detail="Payout information required")

        payout = Payout(
            partner_id=user.id,
            requested_amount=requested,
            total_amount=total,
            fee_mmk=form.fee_mmk or Decimal("0"),
            status=PayoutStatusEnum.pending,
            details=profile.payout_details,
        )
        db.add(payout)
        db.flush()
        for commission in selected:
            db.add(
                PayoutItem(
                    payout_id=payout.id,
                    commission_id=commission.id,
                    amount=commission.amount,
                )
            )
        db.commit()
        db.refresh(payout)
    return {
        "id": payout.id,
        "requested_amount": str(payout.requested_amount),
        "total_amount": str(payout.total_amount),
        "fee_mmk": str(payout.fee_mmk),
        "net_amount": str(Decimal(payout.total_amount) - Decimal(payout.fee_mmk or 0)),
    }


class PayoutResponse(BaseModel):
    id: str
    requested_amount: Decimal
    total_amount: Decimal
    fee_mmk: Decimal
    net_amount: Decimal
    status: PayoutStatusEnum
    reference: str | None = None
    details: Any | None = None
    created_at: int


@router.get("/payouts", response_model=List[PayoutResponse])
def list_payouts(user=Depends(get_verified_user)):
    with get_db() as db:
        payouts = (
            db.query(Payout)
            .filter(Payout.partner_id == user.id)
            .order_by(Payout.created_at.desc())
            .all()
        )
    results: List[PayoutResponse] = []
    for p in payouts:
        details = decrypt_details(p.details) if p.details else None
        net = Decimal(p.total_amount) - Decimal(p.fee_mmk or 0)
        results.append(
            PayoutResponse(
                id=p.id,
                requested_amount=p.requested_amount,
                total_amount=p.total_amount,
                fee_mmk=p.fee_mmk,
                net_amount=net,
                status=p.status,
                reference=p.reference,
                details=details,
                created_at=p.created_at,
            )
        )
    return results
