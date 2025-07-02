import logging
import requests
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from open_webui.env import LITELLM_MASTER_KEY, LITELLM_URL

from open_webui.models.billing import PaymentStatusEnum
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.billing import (
    UserCreditsModel, UserCreditsForm, CreditTransactionModel,
    CreditTransactionForm, PaymentOrderModel, PaymentOrderForm,
    PaymentCallbackForm, UserCredits, CreditTransactions, PaymentOrders
)

from open_webui.storage.provider import Storage

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

router = APIRouter()

# -------------------------
# User Credits Endpoints
# -------------------------

@router.post('/credits', response_model=UserCreditsModel)
async def create_credits(
    form: UserCreditsForm,
    user=Depends(get_admin_user)
):
    """Admin: initialize a user's credit wallet"""
    return UserCredits.insert_new_user_credits(form.user_id, form)

@router.get('/credits', response_model=UserCreditsModel)
async def get_credits(
    user=Depends(get_verified_user)
):
    """Retrieve current user's credit balance"""
    result = UserCredits.get_user_credits(user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT()
        )
    return result

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

@router.post("/orders", response_model=PaymentOrderModel)
async def create_order(
    form: PaymentOrderForm = Depends(),
    screenshot: UploadFile = File(...),
    user=Depends(get_verified_user),
):
    """
    Create a new payment order (credit pack, upgrade, or plan renewal)
    and save the money-transfer screenshot via the configured Storage.
    """

    if not screenshot.filename:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Please upload a valid payment screenshot."
        )

    order = PaymentOrders.create_payment_order(user.id, form)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )

    try:
        # tag with order_id and user_id for future lookup
        tags = {"order_id": order.order_id, "user_id": user.id}
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

    # 3) Attach the file path to the order
    updated = PaymentOrders.save_screenshot_path(order.order_id, path)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to associate screenshot with order"
        )

    # 4) Return the order, now including `screenshot_path`
    return updated

@router.post('/orders/confirm', response_model=PaymentOrderModel)
async def confirm_order(
    order_id: str = Body(..., embed=True),
    admin=Depends(get_admin_user)
):
    """Admin: confirm a payment order after manual verification"""
    # 1. Update order status to 'paid'
    order = PaymentOrders.update_payment_order_status(
        order_id,
        PaymentCallbackForm(order_id=order_id, status=PaymentStatusEnum.paid)
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
                updated_credits = UserCredits.update_credits(order.user_id, order.credits)
                if updated_credits:
                    log.info(f"Added {order.credits} credits to existing wallet for user {order.user_id}. New balance: {updated_credits.credit_balance}")
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
        await register_litellm_customer(order.user_id, order.plan_id)
        log.info(f"Successfully registered user {order.user_id} with LiteLLM for plan {order.plan_id}")
    except Exception as litellm_error:
        log.error(f"Failed to register user {order.user_id} with LiteLLM: {litellm_error}")
        # Log error but don't fail the confirmation

    return order

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
