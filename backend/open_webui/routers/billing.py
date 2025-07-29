import logging
import requests
import time
from typing import Optional, List, Annotated
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body, Form, Query
from pydantic import Field

from open_webui.models.discount import UserDiscountForm
from open_webui.env import LITELLM_MASTER_KEY, LITELLM_URL

from open_webui.models.billing import PaymentStatusEnum, OrderTypeEnum, PlanEnum
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.billing import (
    UserCreditsModel, UserCreditsForm, CreditTransactionModel,
    CreditTransactionForm, PaymentOrderModel, PaymentOrderForm,
    PaymentCallbackForm, PaymentOrderWithUserModel, PaymentOrderAuditForm,
    UserCredits, CreditTransactions, PaymentOrders, PaymentOrderAudits,
    AdminPaymentOrderForm
)
from open_webui.models.plans import Plans, PlanModel

from open_webui.storage.provider import Storage

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

router = APIRouter()


class PlanPublicModel(PlanModel):
    description: Optional[str] = Field(None, exclude=True)
    price: float = Field(exclude=True)
    credits: int  = Field(exclude=True)


class UserCreditsWithPlanModel(UserCreditsModel):
    credit_balance: int = Field(exclude=True)
    monthly_quota: int = Field(exclude=True)
    plan: Optional[PlanPublicModel] = None


# -------------------------
# User Credits Endpoints
# -------------------------

@router.post('/credits', response_model=UserCreditsModel)
async def create_credits(
        form: UserCreditsForm,
        user=Depends(get_admin_user)
):
    """Admin: initialize a user's credit wallet"""
    result = UserCredits.insert_new_user_credits(form.user_id, form)

    # Track manual credit creation
    if result:
        log.info(f"Manual credit creation: admin {user.id} ({user.email}) created {form.credit_balance} credits for user {form.user_id}, plan {form.plan_id}")

    return result


@router.get('/credits', response_model=UserCreditsWithPlanModel)
async def get_credits(
        user=Depends(get_verified_user)
):
    """Retrieve current user's credit balance and associated plan"""
    user_credits = UserCredits.get_user_credits(user.id)
    if not user_credits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT
        )

    current_plan = Plans.get_plan_by_id(user_credits.plan_id)

    return UserCreditsWithPlanModel(
        **user_credits.model_dump(),
        plan=current_plan
    )


@router.get('/{user_id}/credits', response_model=UserCreditsModel)
async def get_user_credits(
        user_id: str,
        admin=Depends(get_admin_user)
):
    """Admin: get credit information for a specific user"""
    result = UserCredits.get_user_credits(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT()
        )
    return result


# @router.post('/credits/debit', response_model=UserCreditsModel)
# async def debit_credits(
#     delta: int,
#     user=Depends(get_verified_user)
# ):
#     """Debit credits after a LiteLLM call"""
#     result = UserCredits.update_credits(user.id, -delta)
#     if not result:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=ERROR_MESSAGES.DEFAULT()
#         )
#     return result

# -------------------------
# Credit Transactions Endpoints
# -------------------------

@router.get('/transactions', response_model=List[CreditTransactionModel])
async def list_transactions(
        skip: int = 0,
        limit: int = 50,
        user=Depends(get_verified_user)
):
    """List recent credit transactions for current user"""
    return CreditTransactions.get_transactions_by_user(user.id, skip, limit)


@router.get('/{user_id}/transactions', response_model=List[CreditTransactionModel])
async def get_user_transactions(
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        admin=Depends(get_admin_user)
):
    """Admin: get transactions for a specific user"""
    return CreditTransactions.get_transactions_by_user(user_id, skip, limit)


# -------------------------
# Payment Orders Endpoints
# -------------------------

@router.get('/admin/orders', response_model=List[PaymentOrderWithUserModel])
async def list_all_orders(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        status: Optional[PaymentStatusEnum] = Query(None),
        user_email: Optional[str] = Query(None),
        admin=Depends(get_admin_user)
):
    """Admin: Get all payment orders across all users with filtering"""
    return PaymentOrders.get_all_orders(skip, limit, status, user_email)


@router.post("/admin/orders", response_model=PaymentOrderModel)
async def create_manual_order(
        form: AdminPaymentOrderForm,
        admin=Depends(get_admin_user)
):
    """Admin: Create a manual payment order for a user."""
    order = PaymentOrders.create_manual_payment_order(form.user_id, form)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )

    # Create an audit record for the manual creation
    audit_form = PaymentOrderAuditForm(
        order_id=order.order_id,
        action="create_manual",
        actor_id=admin.id,
        actor_email=admin.email,
        actor_name=admin.name,
        new_status=order.status.value,
        reason=f"Manual order created by admin: {form.notes}",
        audit_metadata={
            "admin_action": True,
            "form_data": form.model_dump_json()
        }
    )
    PaymentOrderAudits.create_audit_record(audit_form)

    return order


@router.put("/admin/orders/{order_id}", response_model=PaymentOrderModel)
async def update_payment_order(
        order_id: str,
        form: AdminPaymentOrderForm,
        admin=Depends(get_admin_user)
):
    """Admin: Update a manual payment order for a user."""
    order = PaymentOrders.update_payment_order(order_id, form)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND
        )

    # Create an audit record for the manual update
    audit_form = PaymentOrderAuditForm(
        order_id=order.order_id,
        action="update_manual",
        actor_id=admin.id,
        actor_email=admin.email,
        actor_name=admin.name,
        new_status=order.status.value,
        reason=f"Manual order updated by admin: {form.notes}",
        audit_metadata={
            "admin_action": True,
            "form_data": form.model_dump_json()
        }
    )
    PaymentOrderAudits.create_audit_record(audit_form)

    return order

@router.post("/orders", response_model=PaymentOrderModel)
async def create_order(
        type: Annotated[OrderTypeEnum, Form()],
        amount_mmk: Annotated[float, Form()],
        provider: Annotated[str, Form()],
        plan_id: Annotated[Optional[str], Form()] = None,
        plan_target: Annotated[Optional[str], Form()] = None,
        credits: Annotated[Optional[int], Form()] = None,
        discount_code: Annotated[Optional[str], Form()] = None,
        screenshot: UploadFile = File(...),
        user=Depends(get_verified_user),
):
    """
    Create a new payment order (credit pack, upgrade, or plan renewal)
    and save the money-transfer screenshot via the configured Storage.

    Optional discount_code parameter can be provided to apply discounts.
    """
    from open_webui.models.discount import UserDiscounts, DiscountCodes

    if not screenshot.filename:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Please upload a valid payment screenshot."
        )

    # Convert form fields to PaymentOrderForm
    form = PaymentOrderForm(
        type=type,
        amount_mmk=amount_mmk,
        provider=provider,
        plan_id=plan_id,
        plan_target=plan_target,
        credits=credits
    )

    # Check if discount code was provided and is valid
    original_amount = form.amount_mmk
    applied_discount = None

    if discount_code:
        # Validate the discount code
        discount_validation = DiscountCodes.validate_discount_code(discount_code)
        if discount_validation.valid:
            # Calculate discounted amount
            discount_percent = discount_validation.discount_percent
            discount_amount = Decimal(original_amount) * (Decimal(discount_percent) / Decimal(100))
            discounted_amount = Decimal(original_amount) - discount_amount

            # Update the form with discounted amount
            form.amount_mmk = float(discounted_amount.quantize(Decimal('0.01')))
            applied_discount = {
                "code": discount_code,
                "percent": discount_percent,
                "original_amount": original_amount,
                "discount_amount": float(discount_amount.quantize(Decimal('0.01'))),
                "final_amount": form.amount_mmk
            }

            log.info(f"Applied discount code {discount_code} ({discount_percent}%) to order. "
                     f"Original: {original_amount}, Discounted: {form.amount_mmk}")
        else:
            # Invalid discount code, but we'll continue with the order
            log.warning(f"Invalid discount code provided: {discount_code}. Reason: {discount_validation.message}")

    # Check for existing pending orders
    if PaymentOrders.has_pending_order(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending payment order. Please wait for it to be processed before submitting another."
        )

    # Create the payment order with the potentially discounted amount
    order = PaymentOrders.create_payment_order(user.id, form)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )

    try:
        # tag with order_id and user_id for future lookup
        tags = {"order_id": order.order_id, "user_id": user.id}
        if applied_discount:
            tags["discount_code"] = applied_discount["code"]
            tags["discount_percent"] = str(applied_discount["percent"])

        # give it a unique filename
        filename = f"{order.order_id}_{screenshot.filename}"
        contents, path = Storage.upload_file(screenshot.file, filename, tags)
        log.info(f"Saved screenshot for order {order.order_id} at {path}")
    except Exception as e:
        log.exception(f"Failed to save screenshot for order {order.order_id}")
        # you might choose to delete the order here or mark it 'failed'
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save payment screenshot"
        )

    # Attach the file path to the order
    updated = PaymentOrders.save_screenshot_path(order.order_id, path)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to associate screenshot with order"
        )

    # If we successfully applied a discount code, record its usage
    if applied_discount and discount_validation and discount_validation.valid:
        try:
            UserDiscounts.apply_discount(UserDiscountForm(user_id=user.id, discount_code=discount_code))
            log.info(f"Recorded discount code usage for user {user.id}, code {discount_code}")
        except Exception as e:
            # Don't fail the whole transaction if discount recording fails
            log.error(f"Failed to record discount code usage: {e}")

    # Return the order, now including `screenshot_path`
    # Notify admins via Telegram
    try:
        from open_webui.telegram_bot import notify_admins
        from open_webui.config import WEBUI_URL
        from datetime import datetime
        order_creation_date = datetime.fromtimestamp(order.created_at).strftime("%d %b %Y %H:%M")

        user_info = f"👤 User: {user.name} ({user.email}, ID: {user.id})"
        order_details = (
            f"🧾 Order ID: {order.order_id}\n"
            f"💰 Amount: {order.amount_mmk:,} MMK\n"
            f"📦 Plan: {str(order.plan_id.value).capitalize()}\n"
            f"📆 Order Date: {order_creation_date}\n"
        )
        message = (
            f"💳 *New Payment Submitted!*\n\n"
            f"{user_info}\n\n"
            f"{order_details}\n\n"
            f"🔍 Please verify at:\n{WEBUI_URL.value}/admin/billing"
        )

        import asyncio
        asyncio.create_task(notify_admins(message))
    except Exception as e:
        log.error(f"Failed to send Telegram notification for new order {order.order_id}: {e}")

    return updated


@router.patch('/admin/orders/{order_id}/confirm', response_model=PaymentOrderModel)
async def confirm_order(
        order_id: str,
        admin=Depends(get_admin_user)
):
    """Admin: confirm a payment order after manual verification"""
    log.info(f"Admin {admin.id} attempting to confirm order {order_id}")

    # Create audit form
    audit_form = PaymentOrderAuditForm(
        order_id=order_id,
        action="confirm",
        actor_id=admin.id,
        actor_email=admin.email,
        actor_name=admin.name,
        new_status="paid",
        reason="Order confirmed by admin",
        audit_metadata={
            "admin_action": True,
            "timestamp": int(time.time())
        }
    )

    # 1. Update order status to 'paid'
    order = PaymentOrders.update_payment_order_status(
        order_id,
        PaymentCallbackForm(order_id=order_id, status=PaymentStatusEnum.paid),
        audit_form=audit_form
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT()
        )

    # 2. Allocate credits based on the order (if credits > 0)
    if order.credits and order.credits > 0:
        try:
            # Check if user already has a credit wallet
            existing_credits = UserCredits.get_user_credits(order.user_id)

            if existing_credits:
                # User has existing credits - add to their balance
                updated_credits = None
                if order.type == OrderTypeEnum.plan_payment or order.type == OrderTypeEnum.manual:
                    updated_credits = UserCredits.update_subscription(user_id=order.user_id, new_plan=order.plan_id,
                                                                      monthly_quota=order.credits,
                                                                      new_end=order.period_end)
                elif order.type == OrderTypeEnum.credit:
                    updated_credits = UserCredits.update_credits(order.user_id, order.credits)
                elif order.type == OrderTypeEnum.upgrade:
                    updated_credits = UserCredits.update_subscription(user_id=order.user_id, new_plan=order.plan_target,
                                                                      monthly_quota=order.credits,
                                                                      new_end=order.period_end)

                if updated_credits:
                    log.info(
                        f"Added {order.credits} credits to existing wallet for user {order.user_id}. New balance: {updated_credits.credit_balance}")
                    try:
                        from open_webui.models.groups import Groups
                        group_name = str(order.plan_id.value).capitalize()
                        log.info(f"Assigning group {group_name} to user {order.user_id}")
                        result = Groups.sync_user_groups_by_group_names(order.user_id, [group_name])

                        if result:
                            log.info(f"Successfully assigned user {order.user_id} to {group_name} group")
                        else:
                            log.warning(f"Failed to assign user {order.user_id} to {group_name} group - group may not exist")

                    except Exception as e:
                        log.error(f"Exception assigning user {order.user_id} to free group: {e}")
                        return False
                else:
                    log.error(f"Failed to update credits for existing user {order.user_id}")
            else:
                # User doesn't have credits yet - create new wallet
                credit_form = UserCreditsForm(
                    user_id=order.user_id,
                    plan_id=order.plan_id,
                    credit_balance=order.credits,
                    monthly_quota=order.credits,
                    current_period_end=order.period_end
                )
                new_credits = UserCredits.insert_new_user_credits(order.user_id, credit_form)
                if new_credits:
                    log.info(f"Created new credit wallet with {order.credits} credits for user {order.user_id}")
                else:
                    log.error(f"Failed to create credit wallet for user {order.user_id}")

            # Record the credit allocation transaction
            try:
                CreditTransactions.insert_transaction(
                    order.user_id,
                    CreditTransactionForm(
                        tx_id=f"payment_{order.order_id}",
                        delta=order.credits,  # Positive delta for credit addition
                        usd_spend=0.0,  # This is a purchase, not usage
                        model_name="plan_purchase"
                    )
                )
                log.info(f"Recorded credit allocation transaction for order {order_id}")
            except Exception as tx_error:
                log.error(f"Failed to record credit transaction for order {order_id}: {tx_error}")
                # Don't fail the whole operation for transaction logging failure

        except Exception as credit_error:
            log.error(f"Failed to allocate credits for order {order_id}: {credit_error}")
            # Log error but don't fail the payment confirmation
            # Consider adding a flag to track credit allocation failures
    else:
        log.info(f"No credits to allocate for order {order_id} (credits: {order.credits})")

    # 3. Register with LiteLLM (existing functionality)
    try:
        await register_litellm_customer(order.user_id, order.plan_id.value)
        log.info(f"Successfully registered user {order.user_id} with LiteLLM for plan {order.plan_id}")
    except Exception as litellm_error:
        log.error(f"Failed to register user {order.user_id} with LiteLLM: {litellm_error}")
        # Log error but don't fail the confirmation

    # 4. Track subscription completion analytics
    log.info(f"Subscription completed for user {order.user_id}, order {order_id}, plan {order.plan_id}, credits {order.credits}")

    # 5. Notify user via Telegram
    try:
        from open_webui.telegram_bot import send_telegram_message
        from open_webui.models.users import Users
        from datetime import datetime

        # We need the user's telegram_chat_id
        user_to_notify = Users.get_user_by_id(order.user_id)
        if user_to_notify and user_to_notify.telegram_chat_id:
            period_end_str = datetime.fromtimestamp(order.period_end).strftime("%d %b %Y")
            message = (
                f"✅ Payment Confirmed!\n\n"
                f"📦 Plan: {str(order.plan_id.value).capitalize()}\n"
                f"📆 Valid Until: {period_end_str}\n\n"
                f"🙏 Thank you for your purchase!"
            )

            import asyncio
            asyncio.create_task(send_telegram_message(user_to_notify.telegram_chat_id, message))
    except Exception as e:
        log.error(f"Failed to send Telegram notification for confirmed order {order_id}: {e}")

    return order


@router.patch('/admin/orders/{order_id}/decline', response_model=PaymentOrderModel)
async def decline_order(
        order_id: str,
        admin=Depends(get_admin_user)
):
    """Admin: decline a payment order after manual verification"""
    log.info(f"Admin {admin.id} attempting to decline order {order_id}")

    # Update order status to 'declined' with audit tracking
    try:
        # Create audit form
        audit_form = PaymentOrderAuditForm(
            order_id=order_id,
            action="decline",
            actor_id=admin.id,
            actor_email=admin.email,
            actor_name=admin.name,
            new_status="declined",
            reason="Order declined by admin",
            audit_metadata={
                "admin_action": True,
                "timestamp": int(time.time())
            }
        )

        order = PaymentOrders.update_payment_order_status(
            order_id,
            PaymentCallbackForm(order_id=order_id, status=PaymentStatusEnum.declined),
            audit_form=audit_form
        )

        if not order:
            log.warning(f"Order {order_id} not found for decline request")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.DEFAULT()
            )

        log.info(f"Order {order_id} has been successfully declined by admin {admin.id} ({admin.email})")
        return order

    except HTTPException:
        # Re-raise HTTP exceptions (like 409 Conflict)
        raise
    except Exception as e:
        log.error(f"Unexpected error declining order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while declining the order"
        )


@router.get('/orders', response_model=List[PaymentOrderModel])
async def list_orders(
        skip: int = 0,
        limit: int = 50,
        user=Depends(get_verified_user)
):
    """List payment orders for current user"""
    return PaymentOrders.get_orders_by_user(user.id, skip, limit)


@router.get('/{user_id}/orders', response_model=List[PaymentOrderModel])
async def list_user_orders(
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        admin=Depends(get_admin_user)
):
    """Admin: List payment orders for a specific user"""
    return PaymentOrders.get_orders_by_user(user_id, skip, limit)


async def register_litellm_customer(user_id: str, budget_id: str):
    """Register a new customer with LiteLLM"""
    headers = {
        "Authorization": f"Bearer {LITELLM_MASTER_KEY}"
    }
    payload = {
        "user_id": user_id,
        "budget_id": budget_id
    }
    response = requests.post(
        f"{LITELLM_URL}/customer/new",
        headers=headers,
        json=payload
    )

    if not response.ok:
        error_message = "Failed to register with LiteLLM"
        try:
            error_json = response.json()
            if "error" in error_json and "message" in error_json["error"]:
                error_message = error_json["error"]["message"]
        except:
            pass

        log.error(f"Failed to register customer with LiteLLM: {response.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    return response.json()
