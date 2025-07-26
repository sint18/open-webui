from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.models.plans import Plans, PlanForm, PlanModel, PlanTypeEnum
from utils.auth import get_admin_user

router = APIRouter()

@router.post("", response_model=PlanModel, status_code=status.HTTP_201_CREATED)
def create_plan(form_data: PlanForm, admin=Depends(get_admin_user)):
    """
    Create a new plan.
    """
    plan = Plans.insert_plan(form_data)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create plan",
        )
    return plan

@router.get("/{plan_id}", response_model=PlanModel)
def get_plan(plan_id: str):
    """
    Retrieve a plan by its ID.
    """
    plan = Plans.get_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )
    return plan

@router.get("", response_model=List[PlanModel])
def get_all_plans():
    """
    Retrieve all plans.
    """
    plans = Plans.get_plans()
    return plans

@router.put("/{plan_id}", response_model=PlanModel)
def update_plan(plan_id: str, form_data: PlanForm, admin=Depends(get_admin_user)):
    """
    Update an existing plan.
    """
    plan = Plans.update_plan(plan_id, form_data)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or update failed",
        )
    return plan

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: str, admin=Depends(get_admin_user)):
    """
    Delete a plan by its ID.
    """
    success = Plans.delete_plan(plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or deletion failed",
        )
    return
