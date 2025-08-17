import csv
import io
import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select

from open_webui.internal.db import get_db
from open_webui.models.affiliate import Payout, PayoutItem
from open_webui.utils.auth import get_admin_or_support_user

router = APIRouter()


@router.post("/payouts/{payout_id}/approve")
def approve_payout(payout_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        payout = db.get(Payout, payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")

        items = db.query(PayoutItem).filter(PayoutItem.payout_id == payout_id).all()
        approved_sum = sum(item.amount for item in items)

        payout.status = "approved"
        payout.approved_mmk = approved_sum
        db.commit()
    return {"id": payout_id, "status": "approved", "approved_mmk": str(approved_sum)}


@router.post("/payouts/{payout_id}/mark-paid")
def mark_paid(payout_id: str, admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        payout = db.get(Payout, payout_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        payout.status = "paid"
        db.commit()
    return {"id": payout_id, "status": "paid"}


@router.get("/payouts/export")
def export_payouts(admin=Depends(get_admin_or_support_user)):
    with get_db() as db:
        payouts = db.execute(select(Payout)).scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id",
        "partner_id",
        "requested_amount",
        "total_amount",
        "approved_mmk",
        "fee_mmk",
        "status",
        "created_at",
    ])
    for p in payouts:
        writer.writerow(
            [
                p.id,
                p.partner_id,
                p.requested_amount,
                p.total_amount,
                p.approved_mmk,
                p.fee_mmk,
                p.status,
                p.created_at,
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
            payout = Payout(
                id=row.get("id") or None,
                partner_id=row["partner_id"],
                requested_amount=row.get("requested_amount", 0),
                total_amount=row.get("total_amount", 0),
                approved_mmk=row.get("approved_mmk"),
                fee_mmk=row.get("fee_mmk", 0),
                status=row.get("status", "pending"),
                created_at=int(row.get("created_at") or time.time()),
            )
            db.merge(payout)
            count += 1
        db.commit()
    return {"imported": count}
