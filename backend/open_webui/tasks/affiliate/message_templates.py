"""Message templates for affiliate lifecycle events."""

from typing import Dict

TEMPLATES: Dict[str, str] = {
    "order_paid": "✅ Order {order_id} has been paid. Amount: {amount}.",
    "commission_created": "💰 Commission {commission_id} for order {order_id} created: {amount}.",
    "commission_approved": "👍 Commission {commission_id} for order {order_id} approved.",
    "commission_paid": "🎉 Commission {commission_id} for order {order_id} paid.",
    "payout_paid": "💸 Payout {payout_id} of {amount} has been sent.",
}
