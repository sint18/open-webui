from fastapi import APIRouter, Depends, HTTPException, Query, status
import time
from open_webui.constants import ERROR_MESSAGES
from open_webui.models.discount import (
    DiscountCodeCreate,
    DiscountCodeResponse,
    DiscountCodeUpdate,
    DiscountCodeValidateResponse,
    DiscountCodes,
    UserDiscountResponse,
    UserDiscounts,
)
from open_webui.utils.auth import get_admin_user, get_verified_user

router = APIRouter()


#########################
# Discount Code Validation
#########################


@router.get("/validate/{code}", response_model=DiscountCodeValidateResponse)
async def validate_discount_code(code: str, user=Depends(get_verified_user)):
    """Validate a discount code"""

    # Validate code format
    if not code or len(code.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discount code cannot be empty",
        )
    # First validate the code
    validation = DiscountCodes.validate_discount_code(code)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.message,
        )

    # Check if user has already used this code
    if UserDiscounts.has_user_used_code(user.id, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already used this discount code",
        )

    # # Apply the discount code
    # result = UserDiscounts.create_user_discount(user.id, code)
    # if not result:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Failed to apply discount code",
    #     )

    return validation


#########################
# User Discount Endpoints
#########################


@router.get("/user", response_model=list[UserDiscountResponse])
async def get_user_discounts(user=Depends(get_verified_user)):
    """Get all discounts used by the current user"""
    return UserDiscounts.get_user_discounts(user.id)


@router.get("/user/{user_id}", response_model=list[UserDiscountResponse])
async def get_user_discounts_by_id(user_id: str, admin=Depends(get_admin_user)):
    """Get all discounts used by a specific user (admin only)"""
    return UserDiscounts.get_user_discounts(user_id)


@router.get("/users/{code}", response_model=list[UserDiscountResponse])
async def get_users_by_discount_code(code: str, admin=Depends(get_admin_user)):
    """Get all users who have used a specific discount code (admin only)"""
    return UserDiscounts.get_discount_users(code)


#########################
# Admin CRUD Operations
#########################


@router.post("", response_model=DiscountCodeResponse)
async def create_discount_code(form_data: DiscountCodeCreate, admin=Depends(get_admin_user)):
    """Create a new discount code (admin only)"""
    # Validate form data
    if not form_data.code or len(form_data.code.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discount code cannot be empty",
        )

    if form_data.discount_percent < 1 or form_data.discount_percent > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discount percentage must be between 1 and 100",
        )

    if form_data.usage_limit is not None and form_data.usage_limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usage limit must be at least 1",
        )

    if form_data.expires_at is not None and form_data.expires_at < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration date cannot be in the past",
        )
    # Check if code already exists
    existing = DiscountCodes.get_discount_code_by_code(form_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Discount code '{form_data.code}' already exists",
        )

    result = DiscountCodes.create_discount_code(form_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create discount code",
        )

    return result


@router.get("", response_model=list[DiscountCodeResponse])
async def get_all_discount_codes(admin=Depends(get_admin_user)):
    """Get all discount codes (admin only)"""
    return DiscountCodes.get_all_discount_codes()


@router.get("/{code_id}", response_model=DiscountCodeResponse)
async def get_discount_code(code_id: int, admin=Depends(get_admin_user)):
    """Get a discount code by ID (admin only)"""
    discount_code = DiscountCodes.get_discount_code_by_id(code_id)
    if not discount_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    return discount_code


@router.get("/code/{code}", response_model=DiscountCodeResponse)
async def get_discount_code_by_code(code: str, admin=Depends(get_admin_user)):
    """Get a discount code by code value (admin only)"""
    discount_code = DiscountCodes.get_discount_code_by_code(code)
    if not discount_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    return discount_code


@router.put("/{code_id}", response_model=DiscountCodeResponse)
async def update_discount_code(code_id: str, form_data: DiscountCodeUpdate, admin=Depends(get_admin_user)):
    """Update a discount code (admin only)"""

    updated = DiscountCodes.update_discount_code(code_id, form_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    return updated


@router.delete("/{code_id}")
async def delete_discount_code(code_id: str, admin=Depends(get_admin_user)):
    """Delete a discount code (admin only)"""
    result = DiscountCodes.delete_discount_code(code_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    return {"message": "Discount code deleted successfully"}