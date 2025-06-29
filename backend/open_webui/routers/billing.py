import logging
import requests
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from open_webui.env import LITELLM_MASTER_KEY, LITELLM_URL

from models.billing import PaymentStatusEnum
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
    return UserCredits.insert_new_user_credits(user.id, form)

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
    order = PaymentOrders.update_payment_order_status(order_id, PaymentCallbackForm(order_id=order_id, status=PaymentStatusEnum.paid))

    await register_litellm_customer(order.user_id, order.plan_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT()
        )
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
