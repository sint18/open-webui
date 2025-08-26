import csv
import io
import time
import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    Payout,
    PayoutItem,
    OutboxEvent,
    PayoutStatusEnum,
    Commission,
    CommissionStatusEnum,
)
from open_webui.models.audit import AuditLog
from open_webui.utils.auth import get_admin_or_support_user, get_admin_user

router = APIRouter()


class PayoutItemSchema(BaseModel):
    id: str
    payout_id: str
    commission_id: str
    amount: Decimal
    created_at: int

    model_config = ConfigDict(from_attributes=True)


class PayoutSchema(BaseModel):
    id: str
    partner_id: str
    requested_amount: Decimal
    total_amount: Decimal
    fee_mmk: Decimal
    status: PayoutStatusEnum
    reference: str | None = None
    approved_mmk: Decimal | None = None
    created_at: int

    model_config = ConfigDict(from_attributes=True)


class PayoutDetail(PayoutSchema):
    items: List[PayoutItemSchema] = []


@router.post("/payouts/{payout_id}/approve")
def approve_payout(payout_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        payout = db.get(Payout, payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")

        items = db.query(PayoutItem).filter(PayoutItem.payout_id == payout_id).all()
        approved_sum = sum(item.amount for item in items)

        before = {
            "status": payout.status.value,
            "approved_mmk": str(payout.approved_mmk) if payout.approved_mmk else None,
        }
        payout.status = PayoutStatusEnum.approved
        payout.approved_mmk = approved_sum
        after = {
            "status": payout.status.value,
            "approved_mmk": str(payout.approved_mmk),
        }
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"payout:{payout_id}",
                action="approve_payout",
                before=before,
                after=after,
                reason=None,
            )
        )
        db.commit()
    return {
        "id": payout_id,
        "status": PayoutStatusEnum.approved,
        "approved_mmk": str(approved_sum),
    }


@router.post("/payouts/{payout_id}/mark-paid")
def mark_paid(payout_id: str, admin=Depends(get_admin_user)):
    with get_db() as db:
        payout = db.get(Payout, payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        before = {"status": payout.status.value}
        payout.status = PayoutStatusEnum.paid
        after = {"status": payout.status.value}

        items = db.query(PayoutItem).filter(PayoutItem.payout_id == payout_id).all()
        commission_ids = [i.commission_id for i in items]
        if commission_ids:
            db.query(Commission).filter(Commission.id.in_(commission_ids)).update(
                {Commission.status: CommissionStatusEnum.paid},
                synchronize_session=False,
            )

        db.add(
            OutboxEvent(
                event_type="payout_paid",
                payload={
                    "payout_id": payout_id,
                    "partner_id": payout.partner_id,
                    "amount": str(payout.total_amount),
                },
            )
        )
        db.add(
            AuditLog(
                actor_id=admin.id,
                resource=f"payout:{payout_id}",
                action="mark_paid",
                before=before,
                after=after,
                reason=None,
            )
        )
        db.commit()
    return {"id": payout_id, "status": PayoutStatusEnum.paid}


@router.get("/payouts", response_model=List[PayoutSchema])
def list_payouts(
    partner_id: Optional[str] = None,
    status: Optional[PayoutStatusEnum] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    admin=Depends(get_admin_or_support_user),
):
    with get_db() as db:
        query = db.query(Payout)
        if partner_id:
            query = query.filter(Payout.partner_id == partner_id)
        if status:
            query = query.filter(Payout.status == status)
        if start:
            query = query.filter(Payout.created_at >= start)
        if end:
            query = query.filter(Payout.created_at <= end)
        payouts = query.order_by(Payout.created_at.desc()).all()
        return [PayoutSchema.model_validate(p, from_attributes=True) for p in payouts]


@router.get("/payouts/{payout_id}", response_model=PayoutDetail)
def get_payout_detail(payout_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        payout = db.get(Payout, payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        items = (
            db.query(PayoutItem)
            .join(Commission, Commission.id == PayoutItem.commission_id)
            .filter(PayoutItem.payout_id == payout_id)
            .order_by(Commission.created_at.asc())
            .all()
        )
        base = PayoutSchema.model_validate(payout, from_attributes=True)
        return PayoutDetail(
            **base.model_dump(),
            items=[
                PayoutItemSchema.model_validate(i, from_attributes=True) for i in items
            ],
        )


@router.get("/payouts/export")
def export_payouts(ids: Optional[str] = None, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        query = db.query(Payout)
        if ids:
            id_list = ids.split(",")
            query = query.filter(Payout.id.in_(id_list))
        payouts = query.all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "partner_id",
            "requested_amount",
            "total_amount",
            "approved_mmk",
            "fee_mmk",
            "status",
            "reference",
            "created_at",
        ]
    )
    for p in payouts:
        writer.writerow(
            [
                p.id,
                p.partner_id,
                p.requested_amount,
                p.total_amount,
                p.approved_mmk,
                p.fee_mmk,
                p.status.value,
                p.reference,
                p.created_at,
            ]
        )
    return Response(content=buf.getvalue(), media_type="text/csv")


class ExportItemsForm(BaseModel):
    ids: List[str]


@router.post("/payouts/items/export")
def export_payout_items(
    form: ExportItemsForm, admin=Depends(get_admin_or_support_user)
):
    with get_db() as db:
        items = db.query(PayoutItem).filter(PayoutItem.id.in_(form.ids)).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "payout_id", "commission_id", "amount", "created_at"])
    for item in items:
        writer.writerow(
            [
                item.id,
                item.payout_id,
                item.commission_id,
                item.amount,
                item.created_at,
            ]
        )
    return Response(content=buf.getvalue(), media_type="text/csv")


@router.post("/payouts/import")
async def import_payouts(file: UploadFile, admin=Depends(get_admin_or_support_user)):
    data = (await file.read()).decode()
    reader = csv.DictReader(io.StringIO(data))
    count = 0
    with get_db() as db:
        for row in reader:
            payout_id = row.get("id") or str(uuid.uuid4())
            existing = db.get(Payout, payout_id)
            before = (
                {
                    "status": existing.status.value,
                    "total_amount": str(existing.total_amount),
                }
                if existing
                else None
            )
            payout = Payout(
                id=payout_id,
                partner_id=row["partner_id"],
                requested_amount=row.get("requested_amount", 0),
                total_amount=row.get("total_amount", 0),
                approved_mmk=row.get("approved_mmk"),
                fee_mmk=row.get("fee_mmk", 0),
                status=PayoutStatusEnum(row.get("status", "pending")),
                reference=row.get("reference"),
                created_at=int(row.get("created_at") or time.time()),
            )
            db.merge(payout)
            db.add(
                AuditLog(
                    actor_id=admin.id,
                    resource=f"payout:{payout.id}",
                    action="import_payout",
                    before=before,
                    after={
                        "status": payout.status.value,
                        "total_amount": str(payout.total_amount),
                        "requested_amount": str(payout.requested_amount),
                    },
                    reason=None,
                )
            )
            count += 1
        db.commit()
    return {"imported": count}
