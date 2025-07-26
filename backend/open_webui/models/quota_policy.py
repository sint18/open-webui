
import time
from datetime import datetime
from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    ForeignKey,
    case,
    or_,
)

from open_webui.internal.db import Base, get_db
from open_webui.models.users import Users

Window = Literal["day", "week", "month"]


class QuotaPolicy(Base):
    __tablename__ = "quota_policy"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=True)
    plan_id = Column(String, ForeignKey("plan.id"), nullable=True)
    resource_pattern = Column(String, nullable=False)  # e.g., model:o3 or model:*
    limit = Column(Integer, nullable=False)
    window = Column(String, nullable=False, default="day")
    effective_from = Column(BigInteger, default=lambda: int(time.time()))
    expires_at = Column(BigInteger)


class QuotaPolicyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    plan_id: Optional[str] = None
    resource_pattern: str
    limit: int
    window: Window
    effective_from: int
    expires_at: Optional[int] = None


class Quota(BaseModel):
    limit: int
    window: Window


class QuotaPoliciesTable:
    def get_quota(self, user_id: str, resource: str) -> Quota:
        now = int(time.time())
        with get_db() as db:
            user = Users.get_user_by_id(user_id)
            plan_id = getattr(user, "plan_id", None)

            resource_parts = resource.split(":", 1)
            wildcard_resource = f"{resource_parts[0]}:*"
            resources_to_check = [resource, wildcard_resource]

            # Build query for active policies matching the resource or its wildcard
            query = db.query(QuotaPolicy).filter(
                QuotaPolicy.resource_pattern.in_(resources_to_check),
                QuotaPolicy.effective_from <= now,
                or_(
                    QuotaPolicy.expires_at == None,
                    QuotaPolicy.expires_at > now
                ),
                or_(
                    QuotaPolicy.user_id == user_id,
                    QuotaPolicy.plan_id == plan_id if plan_id else False,
                ),
            )

            # Order by precedence:
            # 1. User-specific policies first
            # 2. Exact resource match first
            query = query.order_by(
                case((QuotaPolicy.user_id == user_id, 0), else_=1),
                case((QuotaPolicy.resource_pattern == resource, 0), else_=1),
            )

            policy = query.first()

            if policy:
                return Quota(limit=policy.limit, window=policy.window)

            # Graceful fallback
            return Quota(limit=0, window="day")


QuotaPolicies = QuotaPoliciesTable()
