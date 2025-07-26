from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.models.quota_policy import QuotaPolicies, QuotaPolicyForm, QuotaPolicyModel, Window
from open_webui.utils.auth import get_admin_user

router = APIRouter()


@router.post("", response_model=QuotaPolicyModel, status_code=status.HTTP_201_CREATED)
def create_quota_policy(form_data: QuotaPolicyForm, user=Depends(get_admin_user)):
    """
    Create a new quota policy (Admin only).
    """
    quota_policy = QuotaPolicies.insert_quota_policy(form_data)
    if not quota_policy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quota policy",
        )
    return quota_policy


@router.get("/{policy_id}", response_model=QuotaPolicyModel)
def get_quota_policy(policy_id: str, user=Depends(get_admin_user)):
    """
    Retrieve a quota policy by its ID (Admin only).
    """
    quota_policy = QuotaPolicies.get_quota_policy_by_id(policy_id)
    if not quota_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quota policy not found",
        )
    return quota_policy


@router.get("", response_model=List[QuotaPolicyModel])
def get_all_quota_policies(
        user_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        user=Depends(get_admin_user)
):
    """
    Retrieve all quota policies, optionally filtered by user_id or plan_id (Admin only).
    """
    quota_policies = QuotaPolicies.get_quota_policies(user_id=user_id, plan_id=plan_id)
    return quota_policies


@router.put("/{policy_id}", response_model=QuotaPolicyModel)
def update_quota_policy(policy_id: str, form_data: QuotaPolicyForm, user=Depends(get_admin_user)):
    """
    Update an existing quota policy (Admin only).
    """
    quota_policy = QuotaPolicies.update_quota_policy(policy_id, form_data)
    if not quota_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quota policy not found or update failed",
        )
    return quota_policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quota_policy(policy_id: str, user=Depends(get_admin_user)):
    """
    Delete a quota policy by its ID (Admin only).
    """
    success = QuotaPolicies.delete_quota_policy(policy_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quota policy not found or deletion failed",
        )
    return
