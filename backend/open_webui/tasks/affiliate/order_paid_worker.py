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
    """Persist an order attribution record if it does not exist."""
    with get_db() as db:
        existing = db.execute(
            select(OrderAttribution).where(
                OrderAttribution.order_id == order_id,
                OrderAttribution.attribution_id == attribution_id,
            )
        ).scalar_one_or_none()
        if existing:
            return
        record = OrderAttribution(order_id=order_id, attribution_id=attribution_id)
        db.add(record)
        db.commit()


def _create_commissions(order_id: str, partner_id: str, order_amount: Decimal) -> None:
    """Create pending commission records based on configured rates."""
    with get_db() as db:
        for ctype, rate in PLAN_COMMISSION_RATES.items():
            amount = order_amount * rate
            commission = Commission(
                partner_id=partner_id,
                order_id=order_id,
                type=ctype,
                amount=amount,
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
    """Consume unprocessed order_paid outbox events."""
    with get_db() as db:
        events = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.event_type == "order_paid",
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

        if attribution_id and order_id:
            _persist_order_attribution(order_id, attribution_id)
        if order_id and partner_id and amount:
            _create_commissions(order_id, partner_id, amount)

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
