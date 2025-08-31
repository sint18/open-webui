import enum
import time
import uuid
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Column,
    String,
    Text,
    BigInteger,
    Integer,
    Float,
    Boolean,
    Enum as SAEnum, JSON
)

from open_webui.internal.db import Base, get_db


class PlanTypeEnum(enum.Enum):
    subscription = "subscription"
    package = "package"
    topup = "topup"
    custom = "custom"


class Plan(Base):
    __tablename__ = "plan"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False, default=0.0)
    credits = Column(Integer, nullable=False, default=0)
    image_credits = Column(Integer, nullable=False, default=0)
    video_credits = Column(Integer, nullable=False, default=0)
    plan_type = Column(SAEnum(PlanTypeEnum, name="plan_type_enum"), nullable = False, default = PlanTypeEnum.subscription)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))


class PlanModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    price: float
    credits: int
    image_credits: int
    video_credits: int
    plan_type: PlanTypeEnum
    features: dict | None = None
    is_active: bool
    created_at: int
    updated_at: int


class PlanForm(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    credits: int
    image_credits: int = 0
    video_credits: int = 0
    plan_type: PlanTypeEnum
    features: dict | None = None
    is_active: bool = True


class PlansTable:
    def insert_plan(self, form_data: PlanForm) -> Optional[PlanModel]:
        with get_db() as db:
            plan = Plan(**form_data.model_dump())
            db.add(plan)
            db.commit()
            db.refresh(plan)
            return PlanModel.model_validate(plan)

    def get_plan_by_id(self, plan_id: str) -> Optional[PlanModel]:
        with get_db() as db:
            plan = db.query(Plan).filter_by(id=plan_id).first()
            return PlanModel.model_validate(plan) if plan else None

    def get_plan_by_name(self, name: str) -> Optional[PlanModel]:
        """Retrieve a plan by its name."""
        with get_db() as db:
            plan = db.query(Plan).filter_by(name=name).first()
            return PlanModel.model_validate(plan) if plan else None

    def get_plans(self) -> List[PlanModel]:
        with get_db() as db:
            plans = db.query(Plan).all()
            return [PlanModel.model_validate(plan) for plan in plans]

    def update_plan(self, plan_id: str, form_data: PlanForm) -> Optional[PlanModel]:
        with get_db() as db:
            plan = db.query(Plan).filter_by(id=plan_id).first()
            if plan:
                for key, value in form_data.model_dump().items():
                    setattr(plan, key, value)
                plan.updated_at = int(time.time())
                db.commit()
                db.refresh(plan)
                return PlanModel.model_validate(plan)
            return None

    def delete_plan(self, plan_id: str) -> bool:
        with get_db() as db:
            result = db.query(Plan).filter_by(id=plan_id).delete()
            db.commit()
            return result > 0


Plans = PlansTable()
