import logging
import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Text,
    Integer,
    Boolean,
    ForeignKey
)

####################
# Logger setup
####################

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# SQLAlchemy models
####################

class DiscountCode(Base):
    __tablename__ = "discount_code"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(Text, unique=True, nullable=False)
    discount_percent = Column(Integer, nullable=True)
    expires_at = Column(BigInteger, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))


class UserDiscount(Base):
    __tablename__ = "user_discount"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    discount_code = Column(Text, ForeignKey("discount_code.code"), nullable=False)
    applied_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


####################
# Pydantic models
####################

class DiscountCodeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: str
    discount_percent: Optional[int] = None
    expires_at: Optional[int] = None
    usage_limit: Optional[int] = None
    used_count: int = 0
    active: bool = True
    created_at: int
    updated_at: int


class UserDiscountModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    discount_code: str
    applied_at: int


####################
# Forms
####################

class DiscountCodeForm(BaseModel):
    code: str
    discount_percent: Optional[int] = None
    expires_at: Optional[int] = None
    usage_limit: Optional[int] = None
    active: bool = True


class UserDiscountForm(BaseModel):
    user_id: str
    discount_code: str

class DiscountCodeCreate(BaseModel):
    code: str
    discount_percent: int = Field(ge=1, le=100)
    expires_at: Optional[int] = None
    usage_limit: Optional[int] = Field(default=None, ge=1)
    active: bool = True


class DiscountCodeUpdate(BaseModel):
    code: str
    discount_percent: int = Field(default=None, ge=1, le=100)
    expires_at: Optional[int] = None
    usage_limit: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None


class DiscountCodeResponse(BaseModel):
    id: str
    code: str
    discount_percent: int
    expires_at: Optional[int] = None
    usage_limit: Optional[int] = None
    used_count: int
    active: bool
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class DiscountCodeValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_percent: Optional[int] = None
    message: Optional[str] = None


class UserDiscountResponse(BaseModel):
    id: str
    user_id: str
    discount_code: str
    applied_at: int
    created_at: int

    model_config = ConfigDict(from_attributes=True)



####################
# Table classes
####################

class DiscountCodesTable:
    def create_discount_code(self, form: DiscountCodeForm) -> Optional[DiscountCodeModel]:
        with get_db() as db:
            now_ts = int(time.time())
            record = DiscountCode(
                code=form.code,
                discount_percent=form.discount_percent,
                expires_at=form.expires_at,
                usage_limit=form.usage_limit,
                used_count=0,
                active=form.active,
                created_at=now_ts,
                updated_at=now_ts,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return DiscountCodeModel.model_validate(record) if record else None

    def get_discount_code_by_id(self, id: str) -> Optional[DiscountCodeModel]:
        with get_db() as db:
            record = db.query(DiscountCode).filter(DiscountCode.id == id).first()
            return DiscountCodeModel.model_validate(record) if record else None

    def get_discount_code_by_code(self, code: str) -> Optional[DiscountCodeModel]:
        with get_db() as db:
            record = db.query(DiscountCode).filter(DiscountCode.code == code).first()
            return DiscountCodeModel.model_validate(record) if record else None

    def get_all_discount_codes(self, active_only: bool = False) -> list[DiscountCodeModel]:
        with get_db() as db:
            query = db.query(DiscountCode)
            if active_only:
                query = query.filter(DiscountCode.active == True)
            records = query.order_by(DiscountCode.created_at.desc()).all()
            return [DiscountCodeModel.model_validate(record) for record in records]

    def update_discount_code(self, id: str, form: DiscountCodeForm) -> Optional[DiscountCodeModel]:
        with get_db() as db:
            record = db.query(DiscountCode).filter(DiscountCode.id == id).first()
            if not record:
                return None

            record.code = form.code
            record.discount_percent = form.discount_percent
            record.expires_at = form.expires_at
            record.usage_limit = form.usage_limit
            record.active = form.active
            record.updated_at = int(time.time())

            db.commit()
            db.refresh(record)
            return DiscountCodeModel.model_validate(record)

    def validate_discount_code(self, code: str) -> DiscountCodeValidateResponse:
        """Validate a discount code"""
        with get_db() as db:
            discount_code = db.query(DiscountCode).filter(DiscountCode.code == code).first()
            if not discount_code:
                return DiscountCodeValidateResponse(
                    valid=False,
                    code=code,
                    message="Invalid discount code"
                )

            # Check if code is active
            if not discount_code.active:
                return DiscountCodeValidateResponse(
                    valid=False,
                    code=code,
                    message="Discount code is not active"
                )

            # Check if code has expired
            current_time = int(time.time())
            if discount_code.expires_at and discount_code.expires_at < current_time:
                return DiscountCodeValidateResponse(
                    valid=False,
                    code=code,
                    message="Discount code has expired"
                )

            # Check if usage limit has been reached
            if discount_code.usage_limit and discount_code.used_count >= discount_code.usage_limit:
                return DiscountCodeValidateResponse(
                    valid=False,
                    code=code,
                    message="Discount code usage limit reached"
                )

            return DiscountCodeValidateResponse(
                valid=True,
                code=code,
                discount_percent=discount_code.discount_percent
            )

    def increment_used_count(self, code: str) -> Optional[DiscountCodeModel]:
        with get_db() as db:
            record = db.query(DiscountCode).filter(DiscountCode.code == code).first()
            if not record:
                return None

            record.used_count += 1
            record.updated_at = int(time.time())

            # Check if usage limit has been reached
            if record.usage_limit is not None and record.used_count >= record.usage_limit:
                record.active = False

            db.commit()
            db.refresh(record)
            return DiscountCodeModel.model_validate(record)

    def deactivate_discount_code(self, id: str) -> Optional[DiscountCodeModel]:
        with get_db() as db:
            record = db.query(DiscountCode).filter(DiscountCode.id == id).first()
            if not record:
                return None

            record.active = False
            record.updated_at = int(time.time())

            db.commit()
            db.refresh(record)
            return DiscountCodeModel.model_validate(record)

    def delete_discount_code(self, id: str) -> bool:
        with get_db() as db:
            try:
                record = db.query(DiscountCode).filter(DiscountCode.id == id).first()
                if not record:
                    return False

                db.delete(record)
                db.commit()
                return True
            except Exception as e:
                log.error(f"Error deleting discount code: {e}")
                return False


class UserDiscountsTable:
    def apply_discount(self, form: UserDiscountForm) -> Optional[UserDiscountModel]:
        with get_db() as db:
            # Check if discount code exists and is active
            discount_code = db.query(DiscountCode).filter(
                DiscountCode.code == form.discount_code,
                DiscountCode.active == True
            ).first()

            if not discount_code:
                return None

            # Check if expired
            if discount_code.expires_at and discount_code.expires_at < int(time.time()):
                return None

            # Check if usage limit reached
            if discount_code.usage_limit is not None and discount_code.used_count >= discount_code.usage_limit:
                return None

            # Check if user has already used this code
            existing = db.query(UserDiscount).filter(
                UserDiscount.user_id == form.user_id,
                UserDiscount.discount_code == form.discount_code
            ).first()

            if existing:
                return None

            # Create new user discount record
            now_ts = int(time.time())
            record = UserDiscount(
                user_id=form.user_id,
                discount_code=form.discount_code,
                applied_at=now_ts,
            )

            # Increment the used count on the discount code
            discount_code.used_count += 1
            discount_code.updated_at = now_ts

            # If limit reached, deactivate the code
            if discount_code.usage_limit is not None and discount_code.used_count >= discount_code.usage_limit:
                discount_code.active = False

            db.add(record)
            db.commit()
            db.refresh(record)
            return UserDiscountModel.model_validate(record) if record else None

    def get_user_discounts(self, user_id: str) -> list[UserDiscountModel]:
        with get_db() as db:
            records = db.query(UserDiscount).filter(UserDiscount.user_id == user_id).all()
            return [UserDiscountModel.model_validate(record) for record in records]

    def has_user_used_code(self, user_id: str, code: str) -> bool:
        with get_db() as db:
            record = db.query(UserDiscount).filter(
                UserDiscount.user_id == user_id,
                UserDiscount.discount_code == code
            ).first()
            return record is not None

    def get_discount_users(self, code: str) -> list[UserDiscountModel]:
        with get_db() as db:
            records = db.query(UserDiscount).filter(UserDiscount.discount_code == code).all()
            return [UserDiscountModel.model_validate(record) for record in records]


# Instantiate tables for import
DiscountCodes = DiscountCodesTable()
UserDiscounts = UserDiscountsTable()