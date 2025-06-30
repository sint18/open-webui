import logging
import time
import uuid
from typing import Optional
import enum
import datetime

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Numeric,
    Column,
    String,
    Text,
    Enum as SAEnum,
    Date
)

####################
# Logger setup
####################

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# Enums
####################

class PlanEnum(enum.Enum):
    starter = "starter"
    pro = "pro"
    studio = "studio"


class OrderTypeEnum(enum.Enum):
    credit = "credit"
    upgrade = "upgrade"
    plan_payment = "plan_payment"


class StatusEnum(enum.Enum):
    active = "active"
    grace = "grace"
    expired = "expired"


class PaymentStatusEnum(enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


####################
# SQLAlchemy models
####################

class UserCredit(Base):
    __tablename__ = "user_credit"

    user_id = Column(String, primary_key=True)
    plan_id = Column(SAEnum(PlanEnum, name="plan_enum"), nullable=False)
    credit_balance = Column(BigInteger, nullable=False)
    monthly_quota = Column(BigInteger, nullable=False)
    current_period_end = Column(BigInteger, nullable=True)
    status = Column(SAEnum(StatusEnum, name="status_enum"), nullable=False, default=StatusEnum.active)
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class CreditTransaction(Base):
    __tablename__ = "credit_transaction"

    tx_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    delta = Column(BigInteger, nullable=False)
    usd_spend = Column(Numeric, nullable=False)
    model_name = Column(Text, nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class PaymentOrder(Base):
    __tablename__ = "payment_order"

    order_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    type = Column(SAEnum(OrderTypeEnum, name="order_type_enum"), nullable=False)
    plan_target = Column(Text, nullable=True)
    plan_id = Column(SAEnum(PlanEnum, name="plan_enum"), nullable=True)
    credits = Column(BigInteger, nullable=True)
    amount_mmk = Column(Numeric, nullable=False)
    provider = Column(String, nullable=False)
    status = Column(SAEnum(PaymentStatusEnum, name="payment_status_enum"), nullable=False,
                    default=PaymentStatusEnum.pending)
    period_start = Column(BigInteger, nullable=True)
    screenshot_path = Column(Text, nullable=True)
    period_end = Column(BigInteger, nullable=True)
      # URL or local path of uploaded screenshot
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))
    paid_at = Column(BigInteger, nullable=True)


####################
# Pydantic models & forms
####################

class UserCreditsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    plan_id: PlanEnum
    credit_balance: int
    monthly_quota: int
    current_period_end: Optional[int] = None
    status: StatusEnum
    updated_at: int


class UserCreditsForm(BaseModel):
    plan_id: PlanEnum
    monthly_quota: int
    current_period_end: Optional[int] = None


class CreditTransactionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tx_id: str
    user_id: str
    delta: int
    usd_spend: float
    model_name: str
    created_at: int


class CreditTransactionForm(BaseModel):
    tx_id: str
    delta: int
    usd_spend: float
    model_name: str


class PaymentOrderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    user_id: str
    type: OrderTypeEnum
    plan_target: Optional[str] = None
    plan_id: Optional[PlanEnum] = None
    credits: Optional[int] = None
    amount_mmk: float
    provider: str
    status: PaymentStatusEnum
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    created_at: int
    paid_at: Optional[int] = None
    screenshot_path: Optional[str] = None


class PaymentOrderForm(BaseModel):
    type: OrderTypeEnum
    plan_target: Optional[str] = None
    plan_id: Optional[PlanEnum] = None
    credits: Optional[int] = None
    amount_mmk: float
    provider: str


class PaymentCallbackForm(BaseModel):
    order_id: str
    status: PaymentStatusEnum
    paid_at: Optional[int] = None


####################
# Table classes
####################

class UserCreditsTable:
    def insert_new_user_credits(self, user_id: str, form: UserCreditsForm) -> Optional[UserCreditsModel]:
        with get_db() as db:
            now_ts = int(time.time())
            record = UserCredit(
                user_id=user_id,
                plan_id=form.plan_id,
                credit_balance=form.monthly_quota,
                monthly_quota=form.monthly_quota,
                current_period_end=form.current_period_end,
                status=StatusEnum.active,
                updated_at=now_ts,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return UserCreditsModel.model_validate(record) if record else None

    def get_user_credits(self, user_id: str) -> Optional[UserCreditsModel]:
        with get_db() as db:
            record = db.query(UserCredit).filter(UserCredit.user_id == user_id).first()
            return UserCreditsModel.model_validate(record) if record else None

    def update_credits(self, user_id: str, delta: int) -> Optional[UserCreditsModel]:
        with get_db() as db:
            record = db.query(UserCredit).filter(UserCredit.user_id == user_id).first()
            if record is None:
                return None
            record.credit_balance = record.credit_balance + delta
            record.updated_at = int(time.time())
            db.commit()
            db.refresh(record)
            return UserCreditsModel.model_validate(record)

    def update_subscription(self, user_id: str, new_end: datetime.date) -> Optional[UserCreditsModel]:
        with get_db() as db:
            record = db.query(UserCredit).filter(UserCredit.user_id == user_id).first()
            if not record:
                return None
            record.current_period_end = new_end
            record.status = StatusEnum.active
            record.updated_at = int(time.time())
            db.commit()
            db.refresh(record)
            return UserCreditsModel.model_validate(record)


class CreditTransactionsTable:
    def insert_transaction(
            self, user_id: str, form: CreditTransactionForm
    ) -> Optional[CreditTransactionModel]:
        with get_db() as db:
            now_ts = int(time.time())
            tx_id = form.tx_id if form.tx_id else str(uuid.uuid4())
            record = CreditTransaction(
                tx_id=tx_id,
                user_id=user_id,
                delta=form.delta,
                usd_spend=form.usd_spend,
                model_name=form.model_name,
                created_at=now_ts,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return CreditTransactionModel.model_validate(record) if record else None

    def get_transactions_by_user(
            self, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[CreditTransactionModel]:
        with get_db() as db:
            rows = (
                db.query(CreditTransaction)
                .filter_by(user_id=user_id)
                .order_by(CreditTransaction.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [CreditTransactionModel.model_validate(r) for r in rows]

    def exists(self, tx_id: str):
        with get_db() as db:
            return db.query(CreditTransaction).filter(CreditTransaction.tx_id == tx_id).first() is not None


class PaymentOrdersTable:
    def create_payment_order(
            self, user_id: str, form: PaymentOrderForm
    ) -> Optional[PaymentOrderModel]:
        with get_db() as db:
            now_ts = int(time.time())
            # add 30 days to the incoming period_end timestamp
            period_end_ts = now_ts + int(datetime.timedelta(days=30).total_seconds())
            order_id = str(uuid.uuid4())
            record = PaymentOrder(
                order_id=order_id,
                user_id=user_id,
                type=form.type,
                plan_target=form.plan_target,
                plan_id=form.plan_id,
                credits=form.credits,
                amount_mmk=form.amount_mmk,
                provider=form.provider,
                status=PaymentStatusEnum.pending,
                period_start=now_ts,
                period_end=period_end_ts,
                screenshot_path=None,
                created_at=now_ts,
                paid_at=None,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return PaymentOrderModel.model_validate(record) if record else None

    def save_screenshot_path(
            self, order_id: str, path: str
    ) -> Optional[PaymentOrderModel]:
        """Save the screenshot file path for an existing order."""
        with get_db() as db:
            record = db.query(PaymentOrder).filter(PaymentOrder.order_id == order_id).first()
            if record is None:
                return None
            record.screenshot_path = path
            db.commit()
            db.refresh(record)
            return PaymentOrderModel.model_validate(record)

    def update_payment_order_status(
            self, order_id: str, form: PaymentCallbackForm
    ) -> Optional[PaymentOrderModel]:
        with get_db() as db:
            record = db.query(PaymentOrder).filter(PaymentOrder.order_id == order_id).first()
            if record is None:
                return None
            record.status = form.status
            if form.paid_at:
                record.paid_at = form.paid_at
            if record.type == OrderTypeEnum.plan_payment and record.status == PaymentStatusEnum.paid:
                if record.period_end:
                    user_rec = db.query(UserCredit).filter(UserCredit.user_id == record.user_id).first()
                    if user_rec:
                        user_rec.current_period_end = record.period_end
                        user_rec.status = StatusEnum.active
                        user_rec.updated_at = int(time.time())
            db.commit()
            db.refresh(record)
            return PaymentOrderModel.model_validate(record)

    def get_order_by_id(
            self, order_id: str
    ) -> Optional[PaymentOrderModel]:
        with get_db() as db:
            record = db.query(PaymentOrder).filter(PaymentOrder.order_id == order_id).first()
            return PaymentOrderModel.model_validate(record) if record else None

    def get_orders_by_user(
            self, user_id: str, skip: int = 0, limit: int = 50
    ) -> list[PaymentOrderModel]:
        with get_db() as db:
            rows = (
                db.query(PaymentOrder)
                .filter_by(user_id=user_id)
                .order_by(PaymentOrder.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [PaymentOrderModel.model_validate(r) for r in rows]


# Instantiate tables for import
UserCredits = UserCreditsTable()
CreditTransactions = CreditTransactionsTable()
PaymentOrders = PaymentOrdersTable()
