"""Worker to dispatch affiliate lifecycle notifications."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict

from open_webui.internal.db import get_db
from open_webui.models.affiliate import OutboxEvent
from open_webui.models.users import Users
from open_webui.telegram_bot import send_telegram_message

from .message_templates import TEMPLATES

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 10


async def send_email(to_address: str, subject: str, body: str) -> None:
    """Placeholder email sender."""
    logger.info("Email to %s: %s", to_address, body)


async def _process_outbox_events() -> None:
    with get_db() as db:
        events = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.event_type.in_(list(TEMPLATES.keys())),
                OutboxEvent.processed_at.is_(None),
            )
            .all()
        )

    for event in events:
        payload: Dict[str, Any] = event.payload or {}
        partner_id = payload.get("partner_id")
        user = Users.get_user_by_id(partner_id) if partner_id else None
        template = TEMPLATES.get(event.event_type, "")
        try:
            message = template.format(**payload)
        except Exception:
            logger.exception("Failed to render template %s", event.event_type)
            message = str(payload)

        if user:
            if user.email:
                await send_email(user.email, "Affiliate Update", message)
            if user.telegram_chat_id:
                await send_telegram_message(user.telegram_chat_id, message)

        with get_db() as db:
            db.query(OutboxEvent).filter(OutboxEvent.id == event.id).update(
                {"processed_at": int(time.time())}
            )
            db.commit()


async def worker_loop() -> None:
    """Continuously poll outbox events and send notifications."""
    while True:
        try:
            await _process_outbox_events()
        except Exception:
            logger.exception("Error running affiliate outbox processor loop")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
