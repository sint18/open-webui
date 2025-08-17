"""Worker for processing order-paid events and managing affiliate commissions."""

from __future__ import annotations

import asyncio
import logging
import time
from decimal import Decimal
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from open_webui.internal.db import get_db
from open_webui.models.affiliate import (
    OutboxEvent,
    OrderAttribution,
    Commission,
    CommissionTypeEnum,
    CommissionStatusEnum,
    Payout,
    PayoutItem,
    Attribution,
    Coupon,
    Click,
    AttrViaEnum,
)

logger = logging.getLogger(__name__)

# Default commission rates per type. These could be loaded from configuration.
PLAN_COMMISSION_RATES: Dict[CommissionTypeEnum, Decimal] = {
    CommissionTypeEnum.sale: Decimal("0.10"),
}

# Number of seconds an order should remain pending before auto-approval
LOCK_PERIOD_SECONDS = int(60 * 60 * 24 * 30)  # 30 days

# Poll interval for checking outbox events
POLL_INTERVAL_SECONDS = 10


def _persist_order_attribution(order_id: str, attribution_id: str) -> None:
    """Persist an order attribution record and handle last-click wins."""
    with get_db() as db:
        new_attr = db.get(Attribution, attribution_id)
        if not new_attr:
            return
        existing_records = (
            db.query(OrderAttribution)
            .filter(OrderAttribution.order_id == order_id)
            .all()
        )
        for existing in existing_records:
            if existing.attribution_id != attribution_id:
                prev_attr = db.get(Attribution, existing.attribution_id)
                if prev_attr and prev_attr.partner_id != new_attr.partner_id:
                    existing.lost_to_partner_id = new_attr.partner_id
                    db.query(Commission).filter(
                        Commission.order_id == order_id,
                        Commission.partner_id == prev_attr.partner_id,
                    ).update(
                        {
                            "status": CommissionStatusEnum.rejected,
                            "note": f"Lost attribution to {new_attr.partner_id}",
                        },
                        synchronize_session=False,
                    )
        record = OrderAttribution(order_id=order_id, attribution_id=attribution_id)
        db.add(record)
        db.commit()


def _create_attribution_from_coupon(coupon_code: str) -> tuple[str, str] | None:
    """Create an attribution record when only a coupon code is present."""
    with get_db() as db:
        coupon = (
            db.query(Coupon)
            .filter(Coupon.code == coupon_code, Coupon.active.is_(True))
            .first()
        )
        if not coupon:
            return None
        click = Click(partner_id=coupon.partner_id, coupon_id=coupon.id, user_agent="coupon")
        db.add(click)
        db.commit()
        db.refresh(click)
        attr = Attribution(
            click_id=click.id, partner_id=coupon.partner_id, attr_via=AttrViaEnum.coupon
        )
        db.add(attr)
        db.commit()
        db.refresh(attr)
        return attr.id, coupon.partner_id


def _create_commissions(
    order_id: str,
    partner_id: str,
    order_amount: Decimal,
    *,
    status: CommissionStatusEnum = CommissionStatusEnum.pending,
    note: str | None = None,
) -> None:
    """Create commission records based on configured rates."""
    with get_db() as db:
        for ctype, rate in PLAN_COMMISSION_RATES.items():
            amount = order_amount * rate
            commission = Commission(
                partner_id=partner_id,
                order_id=order_id,
                type=ctype,
                amount=amount,
                status=status,
                note=note,
            )
            db.add(commission)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                logger.debug(
                    "Commission already exists for order %s partner %s type %s",
                    order_id,
                    partner_id,
                    ctype.value,
                )


def _void_commissions(order_id: str, reason: str, only_pending: bool = False) -> None:
    """Set commissions for an order to rejected with a reason."""
    with get_db() as db:
        query = db.query(Commission).filter(Commission.order_id == order_id)
        if only_pending:
            query = query.filter(Commission.status == CommissionStatusEnum.pending)
        updated = query.update(
            {"status": CommissionStatusEnum.rejected, "note": reason},
            synchronize_session=False,
        )
        if updated:
            db.commit()


def _approve_pending_commissions() -> None:
    """Move commissions from pending to approved after lock period."""
    threshold = int(time.time()) - LOCK_PERIOD_SECONDS
    with get_db() as db:
        updated = (
            db.query(Commission)
            .filter(
                Commission.status == CommissionStatusEnum.pending,
                Commission.created_at <= threshold,
            )
            .update({"status": CommissionStatusEnum.approved}, synchronize_session=False)
        )
        if updated:
            db.commit()


def _mark_paid_commissions() -> None:
    """Mark commissions as paid when associated payout is paid."""
    with get_db() as db:
        paid_commission_ids = (
            db.query(PayoutItem.commission_id)
            .join(Payout, Payout.id == PayoutItem.payout_id)
            .filter(Payout.status == "paid")
            .subquery()
        )
        updated = (
            db.query(Commission)
            .filter(
                Commission.status == CommissionStatusEnum.approved,
                Commission.id.in_(paid_commission_ids),
            )
            .update({"status": CommissionStatusEnum.paid}, synchronize_session=False)
        )
        if updated:
            db.commit()


async def _process_outbox_events() -> None:
    """Consume unprocessed affiliate-related outbox events."""
    with get_db() as db:
        events = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.event_type.in_(
                    ["order_paid", "payment_rejected", "order_refunded"]
                ),
                OutboxEvent.processed_at.is_(None),
            )
            .all()
        )

    for event in events:
        payload: Dict[str, Any] = event.payload or {}
        order_id = payload.get("order_id")
        partner_id = payload.get("partner_id")
        amount = Decimal(str(payload.get("amount", "0")))
        attribution_id = payload.get("attribution_id")
        coupon_code = payload.get("coupon_code")
        self_ref = payload.get("self_referral")

        if event.event_type == "order_paid":
            if not attribution_id and coupon_code:
                res = _create_attribution_from_coupon(coupon_code)
                if res:
                    attribution_id, partner_id = res
            if attribution_id and order_id:
                _persist_order_attribution(order_id, attribution_id)
            if order_id and partner_id and amount:
                status = (
                    CommissionStatusEnum.review
                    if self_ref
                    else CommissionStatusEnum.pending
                )
                note = "Self-referral" if self_ref else None
                _create_commissions(
                    order_id,
                    partner_id,
                    amount,
                    status=status,
                    note=note,
                )
        elif event.event_type == "payment_rejected":
            if order_id:
                _void_commissions(order_id, "Payment not verified")
        elif event.event_type == "order_refunded":
            if order_id:
                _void_commissions(order_id, "Refund within lock period", only_pending=True)

        with get_db() as db:
            db.query(OutboxEvent).filter(OutboxEvent.id == event.id).update(
                {"processed_at": int(time.time())}
            )
            db.commit()


async def worker_loop() -> None:
    """Main worker loop to process events and update commission statuses."""
    while True:
        try:
            await _process_outbox_events()
            _approve_pending_commissions()
            _mark_paid_commissions()
        except Exception:
            logger.exception("Error running order_paid_worker loop")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
