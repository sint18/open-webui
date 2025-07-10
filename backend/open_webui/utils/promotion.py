import logging

from open_webui.env import FREE_SIGNUP_CREDITS

log = logging.getLogger(__name__)


def create_free_signup_credits(user_id: str, signup_method: str = "email") -> bool:
    """
    Create free signup credits for a new user.

    Args:
        user_id: The user ID to create credits for
        signup_method: Method used for signup ("email", "oauth", "google", "microsoft", etc.)

    Returns:
        bool: True if credits were created successfully, False otherwise
    """
    try:
        from open_webui.models.billing import UserCredits, PlanEnum, StatusEnum, UserCreditsForm

        # Check if user already has credits (prevent duplicate credits)
        existing_credits = UserCredits.get_user_credits(user_id)
        if existing_credits:
            log.info(f"User {user_id} already has credits, skipping free signup credits")
            return True

        # Create free credits
        credit_data = {
            'user_id': user_id,
            'plan_id': PlanEnum.free,
            'credit_balance': FREE_SIGNUP_CREDITS,
            'monthly_quota': FREE_SIGNUP_CREDITS,
            'current_period_end': None,  # No expiry for free credits
            'status': StatusEnum.active
        }
        log.info(
            f"Creating {FREE_SIGNUP_CREDITS} free signup credits for user {user_id} via {signup_method}"
        )

        result = UserCredits.insert_new_user_credits(user_id=user_id, form=UserCreditsForm(**credit_data))

        assign_user_to_free_group(user_id)

        if result:

            log.info(
                f"Successfully created {FREE_SIGNUP_CREDITS} free signup credits for user {user_id} via {signup_method}")
            return True
        else:
            log.error(f"Failed to create free signup credits for user {user_id} via {signup_method}")
            return False

    except Exception as e:
        log.error(f"Exception creating free signup credits for user {user_id} via {signup_method}: {e}")
        return False


def create_promotional_credits(user_id: str, amount: int, reason: str = "promotion") -> bool:
    """
    Create promotional credits for a user (for future use).

    Args:
        user_id: The user ID to create credits for
        amount: Amount of credits to give
        reason: Reason for the promotional credits

    Returns:
        bool: True if credits were added successfully, False otherwise
    """
    try:
        from open_webui.models.billing import UserCredits

        # Get and update existing credits or create new ones
        existing_credits = UserCredits.update_credits(user_id, amount)
        if not existing_credits:
            # Create new credit record
            from open_webui.models.billing import PlanEnum, StatusEnum, UserCreditsForm
            credit_data = {
                'user_id': user_id,
                'plan_id': PlanEnum.free,
                'credit_balance': amount,
                'monthly_quota': amount,
                'current_period_end': None,
                'status': StatusEnum.active
            }
            existing_credits = UserCredits.insert_new_user_credits(user_id=user_id, form=UserCreditsForm(**credit_data))

        if existing_credits:
            log.info(f"Successfully added {amount} promotional credits for user {user_id} - reason: {reason}")
            return True
        else:
            log.error(f"Failed to add promotional credits for user {user_id}")
            return False

    except Exception as e:
        log.error(f"Exception adding promotional credits for user {user_id}: {e}")
        return False


def assign_user_to_free_group(user_id: str) -> bool:
    """
    Assign user to the "free" group.

    Args:
        user_id: The user ID to assign to free group

    Returns:
        bool: True if assignment was successful, False otherwise
    """
    try:
        from open_webui.models.groups import Groups

        # Try to assign user to "free" group by name
        result = Groups.sync_user_groups_by_group_names(user_id, ["Free"])

        if result:
            log.info(f"Successfully assigned user {user_id} to free group")
            return True
        else:
            log.warning(f"Failed to assign user {user_id} to free group - group may not exist")
            return False

    except Exception as e:
        log.error(f"Exception assigning user {user_id} to free group: {e}")
        return False
