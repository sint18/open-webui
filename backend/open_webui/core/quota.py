from functools import wraps
from fastapi import Request, HTTPException, status
import logging

from open_webui.models.quota_policy import QuotaPolicies

log = logging.getLogger(__name__)

def requires_quota(resource_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = kwargs.get('user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User context required for quota check"
                )

            resource_id = None
            if resource_type == "model":
                body = await request.json()
                model_id = body.get("model")
                if model_id:
                    resource_id = f"model:{model_id}"
            elif resource_type == "image":
                body = await request.json()
                model_name = body.get("model_name")
                if model_name:
                    resource_id = f"image:{model_name}"
            elif resource_type == "upload":
                resource_id = "upload:*"

            if not resource_id:
                return await func(request, *args, **kwargs)

            quota = QuotaPolicies.get_quota(user.id, resource_id)
            log.info(f"Final policy={str(quota.model_dump())}")
            if quota.limit <= 0:
                log.warning(f"Quota limit for resource {resource_id} is disabled for user {user.id}.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this resource.")

            is_allowed = await request.app.state.usage_limiter.check(
                user_id=user.id,
                resource=resource_id,
                limit=quota.limit,
                window=quota.window,
            )

            if not is_allowed:
                log.warning(f"Quota limit for resource {resource_id} exceeded for user {user.id}.")
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
