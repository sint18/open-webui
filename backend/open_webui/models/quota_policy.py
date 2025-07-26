import time
from datetime import datetime
from typing import Optional, Dict, Any, Literal, List
import logging

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
from open_webui.models.billing import UserCredits

Window = Literal["3h", "12h", "day", "week", "month"]
log = logging.getLogger(__name__)


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


class QuotaPolicyForm(BaseModel):
    user_id: Optional[str] = None
    plan_id: Optional[str] = None
    resource_pattern: str
    limit: int
    window: Window
    effective_from: Optional[int] = None
    expires_at: Optional[int] = None


class QuotaPoliciesTable:
    def insert_quota_policy(self, form_data: QuotaPolicyForm) -> Optional[QuotaPolicyModel]:
        with get_db() as db:
            quota_policy = QuotaPolicy(**form_data.model_dump())
            db.add(quota_policy)
            db.commit()
            db.refresh(quota_policy)
            return QuotaPolicyModel.model_validate(quota_policy)

    def get_quota_policy_by_id(self, policy_id: str) -> Optional[QuotaPolicyModel]:
        with get_db() as db:
            policy = db.query(QuotaPolicy).filter_by(id=policy_id).first()
            return QuotaPolicyModel.model_validate(policy) if policy else None

    def get_quota_policies(self, user_id: Optional[str] = None, plan_id: Optional[str] = None) -> List[
        QuotaPolicyModel]:
        with get_db() as db:
            query = db.query(QuotaPolicy)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if plan_id:
                query = query.filter_by(plan_id=plan_id)
            policies = query.all()
            return [QuotaPolicyModel.model_validate(policy) for policy in policies]

    def update_quota_policy(self, policy_id: str, form_data: QuotaPolicyForm) -> Optional[QuotaPolicyModel]:
        with get_db() as db:
            policy = db.query(QuotaPolicy).filter_by(id=policy_id).first()
            if policy:
                for key, value in form_data.model_dump(exclude_unset=True).items():
                    setattr(policy, key, value)
                db.commit()
                db.refresh(policy)
                return QuotaPolicyModel.model_validate(policy)
            return None

    def delete_quota_policy(self, policy_id: str) -> bool:
        with get_db() as db:
            result = db.query(QuotaPolicy).filter_by(id=policy_id).delete()
            db.commit()
            return result > 0

    def get_quota(self, user_id: str, resource: str) -> Quota:
        now = int(time.time())
        with get_db() as db:
            user_credits = UserCredits.get_user_credits(user_id)
            if not user_credits:
                return Quota(limit=0, window="day")

            plan_id = str(user_credits.plan_id)
            resource_parts = resource.split(":", 1)
            wildcard = f"{resource_parts[0]}:*"
            to_check = [resource, wildcard]
            log.info(f"Checking resources: {to_check}")
            # 1. Check user-specific policies
            user_policy = db.query(QuotaPolicy).filter(
                QuotaPolicy.user_id == user_id,
                QuotaPolicy.resource_pattern.in_(to_check),
                QuotaPolicy.effective_from <= now,
                or_(
                    QuotaPolicy.expires_at == None,
                    QuotaPolicy.expires_at > now,
                )
            ).order_by(
                case((QuotaPolicy.resource_pattern == resource, 0), else_=1)
            ).first()
            if user_policy:
                log.info(f"Quota policy {user_policy}")
                return Quota(limit=user_policy.limit, window=user_policy.window)

            # 2. Check plan-wide policies
            plan_policy = db.query(QuotaPolicy).filter(
                QuotaPolicy.plan_id == plan_id,
                QuotaPolicy.resource_pattern.in_(to_check),
                QuotaPolicy.effective_from <= now,
                or_(
                    QuotaPolicy.expires_at == None,
                    QuotaPolicy.expires_at > now,
                )
            ).order_by(
                case((QuotaPolicy.resource_pattern == resource, 0), else_=1)
            ).first()

            if plan_policy:
                log.info(f"Quota policy {plan_policy}")
                return Quota(limit=plan_policy.limit, window=plan_policy.window)

            # 3. Nothing matched
            return Quota(limit=0, window="day")


QuotaPolicies = QuotaPoliciesTable()
