from __future__ import annotations

from starlette_admin import action, fields
from starlette_admin.contrib.sqla import ModelView

from open_webui.admin.fields import EpochDateTimeField
from open_webui.models.billing import (
    PaymentOrder,
    PaymentStatusEnum,
    OrderTypeEnum,
    PaymentOrders as PaymentOrdersTable,
    PaymentOrderAuditForm,
    PaymentCallbackForm,
    UserCredits as UserCreditsTable,
    UserCreditsForm,
    CreditTransactions as CreditTransactionsTable,
    CreditTransactionForm,
)
from open_webui.models.plans import Plans
from open_webui.internal.db import get_db
from typing import List
import time


class PaymentOrderAdmin(ModelView):
    label = "Payment Orders"


    exclude_fields_from_create = ["created_at", "paid_at", "screenshot_path"]
    exclude_fields_from_list = [
        "user_id", "plan_id", "order_id", "created_at", "paid_at"
    ]

    fields = [
        "order_id",
        fields.HasOne("user", identity="user", searchable=True, label="User"),
        fields.EnumField("type", enum=OrderTypeEnum, required=True),
        fields.StringField("plan_target", required=False),
        fields.HasOne("plan", identity="plan", searchable=True, label="Plan"),
        fields.IntegerField("credits", required=False),
        fields.IntegerField("image_credits", required=False),
        fields.IntegerField("video_credits", required=False),
        fields.FloatField("amount_mmk", required=True),
        fields.StringField("provider", required=True),
        fields.EnumField("status", enum=PaymentStatusEnum, required=True),
        EpochDateTimeField("period_start", label="Period Start", read_only=True),
        EpochDateTimeField("period_end", label="Period End", read_only=True),
        EpochDateTimeField("created_at", label="Created", read_only=True),
        EpochDateTimeField("paid_at", label="Paid At", read_only=True),
        fields.TextAreaField("screenshot_path", required=False),
        fields.TextAreaField("notes", required=False),
    ]

    list_columns = [
        "order_id", "user", "type", "plan", "amount_mmk", "provider", "status", "created_at", "paid_at"
    ]

    sortable_fields = [
        "amount_mmk", "status", "created_at", "paid_at"
    ]

    search_fields = ["order_id", "user_id", "plan_id", "provider"]

    actions = ["mark_paid", "mark_declined"]

    @action(name="mark_paid", text="Mark Paid", confirmation="Mark selected orders as paid?", submit_btn_text="Confirm")
    async def mark_paid(self, request, pks: List[str]):
        # Mirror routers.billing.confirm_order behavior per order
        admin_user = getattr(getattr(request, "state", object()), "admin_user", None)
        admin_id = getattr(admin_user, "id", "admin")
        admin_email = getattr(admin_user, "email", None)
        admin_name = getattr(admin_user, "name", None)

        payment_orders = PaymentOrdersTable
        user_credits = UserCreditsTable
        credit_txs = CreditTransactionsTable

        updated, failed = 0, 0
        for order_id in pks:
            try:
                audit_form = PaymentOrderAuditForm(
                    order_id=order_id,
                    action="confirm",
                    actor_id=admin_id,
                    actor_email=admin_email,
                    actor_name=admin_name,
                    new_status="paid",
                    reason="Order confirmed by admin (admin panel)",
                    audit_metadata={
                        "admin_action": True,
                        "timestamp": int(time.time()),
                        "source": "admin_panel",
                    },
                )

                # Atomic status update + audit (handled inside models with transaction)
                order = payment_orders.update_payment_order_status(
                    order_id,
                    PaymentCallbackForm(order_id=order_id, status=PaymentStatusEnum.paid, paid_at=int(time.time())),
                    audit_form=audit_form,
                )

                if not order:
                    failed += 1
                    continue

                # Allocate credits following routers.billing.confirm_order
                if (order.credits and order.credits > 0) or \
                   (order.image_credits and order.image_credits > 0) or \
                   (order.video_credits and order.video_credits > 0):
                    try:
                        existing_credits = user_credits.get_user_credits(order.user_id)

                        if existing_credits:
                            updated_credits = None
                            if order.type == OrderTypeEnum.plan_payment or order.type == OrderTypeEnum.manual:
                                updated_credits = user_credits.update_subscription(
                                    user_id=order.user_id,
                                    new_plan=order.plan_id,
                                    monthly_quota=order.credits or 0,
                                    monthly_image_quota=order.image_credits or 0,
                                    monthly_video_quota=order.video_credits or 0,
                                    new_end=order.period_end,
                                )
                            elif order.type == OrderTypeEnum.credit:
                                updated_credits = user_credits.update_credits(
                                    order.user_id,
                                    order.credits or 0,
                                    image_delta=order.image_credits or 0,
                                    video_delta=order.video_credits or 0,
                                )
                            elif order.type == OrderTypeEnum.upgrade:
                                updated_credits = user_credits.update_subscription(
                                    user_id=order.user_id,
                                    new_plan=order.plan_target,
                                    monthly_quota=order.credits or 0,
                                    monthly_image_quota=order.image_credits or 0,
                                    monthly_video_quota=order.video_credits or 0,
                                    new_end=order.period_end,
                                )

                            if updated_credits:
                                try:
                                    from open_webui.models.groups import Groups
                                    group_name = str(order.plan_id).capitalize()
                                    Groups.sync_user_groups_by_group_names(order.user_id, [group_name])
                                except Exception:
                                    # Non-fatal; keep behavior consistent with router
                                    pass
                        else:
                            credit_form = UserCreditsForm(
                                user_id=order.user_id,
                                plan_id=order.plan_id,
                                credit_balance=order.credits or 0,
                                image_credit_balance=order.image_credits or 0,
                                video_credit_balance=order.video_credits or 0,
                                monthly_quota=order.credits or 0,
                                monthly_image_quota=order.image_credits or 0,
                                monthly_video_quota=order.video_credits or 0,
                                current_period_end=order.period_end,
                            )
                            user_credits.insert_new_user_credits(order.user_id, credit_form)

                        try:
                            if order.credits:
                                credit_txs.insert_transaction(
                                    order.user_id,
                                    CreditTransactionForm(
                                        tx_id=f"payment_{order.order_id}_text",
                                        delta=order.credits,
                                        usd_spend=0.0,
                                        model_name="plan_purchase",
                                    ),
                                )
                            if order.image_credits:
                                credit_txs.insert_transaction(
                                    order.user_id,
                                    CreditTransactionForm(
                                        tx_id=f"payment_{order.order_id}_image",
                                        delta=order.image_credits,
                                        usd_spend=0.0,
                                        model_name="plan_purchase",
                                        resource_type="image",
                                    ),
                                )
                            if order.video_credits:
                                credit_txs.insert_transaction(
                                    order.user_id,
                                    CreditTransactionForm(
                                        tx_id=f"payment_{order.order_id}_video",
                                        delta=order.video_credits,
                                        usd_spend=0.0,
                                        model_name="plan_purchase",
                                        resource_type="video",
                                    ),
                                )
                        except Exception:
                            # Non-fatal; match router behavior
                            pass
                    except Exception:
                        # Non-fatal; match router behavior
                        pass
                # Telegram notification (best-effort), same as router
                try:
                    from open_webui.telegram_bot import send_telegram_message
                    from open_webui.models.users import Users
                    from datetime import datetime

                    user_to_notify = Users.get_user_by_id(order.user_id)
                    if user_to_notify and user_to_notify.telegram_chat_id:
                        period_end_str = datetime.fromtimestamp(order.period_end).strftime("%d %b %Y")
                        plan = Plans.get_plan_by_id(order.plan_id)
                        plan_name = plan.name if plan else str(order.plan_id).capitalize()
                        message = (
                            f"✅ Payment Confirmed!\n\n"
                            f"📦 Plan: {plan_name}\n"
                            f"📅 Valid Until: {period_end_str}\n\n"
                            f"🙏 Thank you for your purchase!"
                        )
                        import asyncio
                        asyncio.create_task(send_telegram_message(user_to_notify.telegram_chat_id, message))
                except Exception:
                    pass

                updated += 1
            except Exception:
                failed += 1

        msg = f"Confirmed {updated} order(s)."
        if failed:
            msg += f" {failed} failed."
        return {"message": msg}

    @action(name="mark_declined", text="Decline", confirmation="Decline selected orders?", submit_btn_text="Decline")
    async def mark_declined(self, request, pks: List[str]):
        # Mirror routers.billing.decline_order behavior per order
        admin_user = getattr(getattr(request, "state", object()), "admin_user", None)
        admin_id = getattr(admin_user, "id", "admin")
        admin_email = getattr(admin_user, "email", None)
        admin_name = getattr(admin_user, "name", None)

        payment_orders = PaymentOrdersTable
        declined, failed = 0, 0
        for order_id in pks:
            try:
                audit_form = PaymentOrderAuditForm(
                    order_id=order_id,
                    action="decline",
                    actor_id=admin_id,
                    actor_email=admin_email,
                    actor_name=admin_name,
                    new_status="declined",
                    reason="Order declined by admin (admin panel)",
                    audit_metadata={
                        "admin_action": True,
                        "timestamp": int(time.time()),
                        "source": "admin_panel",
                    },
                )

                order = payment_orders.update_payment_order_status(
                    order_id,
                    PaymentCallbackForm(order_id=order_id, status=PaymentStatusEnum.declined),
                    audit_form=audit_form,
                )

                if not order:
                    failed += 1
                else:
                    declined += 1
            except Exception:
                failed += 1

        msg = f"Declined {declined} order(s)."
        if failed:
            msg += f" {failed} failed."
        return {"message": msg}


VIEWS = [PaymentOrderAdmin(PaymentOrder, icon="fa-solid fa-file-invoice-dollar")]
