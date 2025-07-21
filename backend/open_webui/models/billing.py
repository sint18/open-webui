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
    Date,
    JSON,
    ForeignKey
)
from fastapi import HTTPException, status

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
    free = "free"


class OrderTypeEnum(enum.Enum):
    credit = "credit"
    upgrade = "upgrade"
    plan_payment = "plan_payment"
    manual = "manual"


class StatusEnum(enum.Enum):
    active = "active"
    grace = "grace"
    expired = "expired"


class PaymentStatusEnum(enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    declined = "declined"


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
    notes = Column(Text, nullable=True)


class PaymentOrderAudit(Base):
    __tablename__ = "payment_order_audit"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("payment_order.order_id"), nullable=False)
    action = Column(String, nullable=False)  # 'confirm', 'decline', 'create'
    actor_id = Column(String, nullable=False)
    actor_email = Column(String, nullable=True)
    actor_name = Column(String, nullable=True)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    audit_metadata = Column(JSON, nullable=True)  # Additional context like IP, user agent
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


####################
# Helper functions for credit usage info
####################

async def get_credit_usage_info(user_id: str) -> dict:
    """Get current credit usage information for piggy-backing in responses"""
    try:
        credits = UserCredits.get_user_credits(user_id)
        if not credits:
            return {}

        used = credits.monthly_quota - credits.credit_balance
        limit = credits.monthly_quota
        percent = (used / limit * 100) if limit > 0 else 0

        return {
            "used": used,
            "limit": limit,
            "percent": round(percent, 1)
        }
    except Exception as e:
        log.error(f"Error getting credit usage info: {e}")
        return {}

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
    user_id: str
    plan_id: PlanEnum
    credit_balance: int  # Add explicit credit_balance field
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
    notes: Optional[str] = None


class PaymentOrderWithUserModel(PaymentOrderModel):
    """Extended payment order model that includes user information"""
    user_name: Optional[str] = None
    user_email: Optional[str] = None


class PaymentOrderForm(BaseModel):
    type: OrderTypeEnum
    plan_target: Optional[str] = None
    plan_id: Optional[PlanEnum] = None
    credits: Optional[int] = None
    amount_mmk: float
    provider: str


class AdminPaymentOrderForm(BaseModel):
    user_id: str
    type: OrderTypeEnum
    plan_target: Optional[str] = None
    plan_id: Optional[PlanEnum] = None
    credits: Optional[int] = None
    amount_mmk: float
    provider: str
    notes: Optional[str] = None




class PaymentCallbackForm(BaseModel):
    order_id: str
    status: PaymentStatusEnum
    paid_at: Optional[int] = None


class PaymentOrderAuditModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    action: str
    actor_id: str
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    audit_metadata: Optional[dict] = None
    created_at: int


class PaymentOrderAuditForm(BaseModel):
    order_id: str
    action: str
    actor_id: str
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    audit_metadata: Optional[dict] = None


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
                credit_balance=form.credit_balance,  # Use form.credit_balance instead of monthly_quota
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

    def update_subscription(self, user_id: str, new_plan: PlanEnum, monthly_quota: int, new_end: datetime.date, new_status: Optional[StatusEnum]=None) -> Optional[UserCreditsModel]:
        with get_db() as db:
            record = db.query(UserCredit).filter(UserCredit.user_id == user_id).first()
            if not record:
                return None
            record.plan_id = new_plan
            record.monthly_quota = monthly_quota
            record.current_period_end = new_end
            record.credit_balance = record.credit_balance + monthly_quota
            record.status = new_status if new_status else StatusEnum.active
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
    def has_pending_order(self, user_id: str) -> bool:
        """Check if user has any pending payment orders"""
        with get_db() as db:
            return db.query(PaymentOrder).filter(
                PaymentOrder.user_id == user_id,
                PaymentOrder.status == PaymentStatusEnum.pending
            ).first() is not None

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

    def create_manual_payment_order(
            self, user_id: str, form: AdminPaymentOrderForm
    ) -> Optional[PaymentOrderModel]:
        with get_db() as db:
            now_ts = int(time.time())
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
                notes=form.notes,
                created_at=now_ts,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return PaymentOrderModel.model_validate(record) if record else None

    def update_payment_order(
            self, order_id: str, form: AdminPaymentOrderForm
    ) -> Optional[PaymentOrderModel]:
        with get_db() as db:
            record = db.query(PaymentOrder).filter(PaymentOrder.order_id == order_id).first()
            if record:
                record.user_id = form.user_id
                record.type = form.type
                record.plan_target = form.plan_target
                record.plan_id = form.plan_id
                record.credits = form.credits
                record.amount_mmk = form.amount_mmk
                record.provider = form.provider
                record.notes = form.notes
                db.commit()
                db.refresh(record)
                return PaymentOrderModel.model_validate(record)
            return None

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
            self, order_id: str, form: PaymentCallbackForm,
            audit_form: Optional[PaymentOrderAuditForm] = None
    ) -> Optional[PaymentOrderModel]:
        with get_db() as db:
            # Use explicit transaction with SELECT FOR UPDATE to prevent race conditions
            try:
                # Start a transaction
                db.begin()

                record = db.query(PaymentOrder).filter(PaymentOrder.order_id == order_id).with_for_update().first()
                if record is None:
                    db.rollback()
                    return None

                # Store previous status for audit
                previous_status = record.status.value

                # Guard against double-handling: only allow status changes from 'pending'
                if record.status != PaymentStatusEnum.pending:
                    # Determine the appropriate error message based on current status
                    if record.status == PaymentStatusEnum.paid:
                        error_detail = f"Order {order_id} is already confirmed/paid and cannot be modified"
                    elif record.status == PaymentStatusEnum.declined:
                        error_detail = f"Order {order_id} is already declined and cannot be modified"
                    elif record.status == PaymentStatusEnum.failed:
                        error_detail = f"Order {order_id} has failed and cannot be modified"
                    else:
                        error_detail = f"Order {order_id} has status '{record.status.value}' and cannot be modified"

                    log.warning(f"Attempted to modify order {order_id} with status {record.status.value}")
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=error_detail
                    )

                # Proceed with status update
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

                # Create audit record if audit_form is provided
                if audit_form:
                    audit_record = PaymentOrderAudit(
                        id=str(uuid.uuid4()),
                        order_id=order_id,
                        action=audit_form.action,
                        actor_id=audit_form.actor_id,
                        actor_email=audit_form.actor_email,
                        actor_name=audit_form.actor_name,
                        previous_status=previous_status,
                        new_status=form.status.value,
                        reason=audit_form.reason,
                        audit_metadata=audit_form.audit_metadata,
                        created_at=int(time.time())
                    )
                    db.add(audit_record)

                # Commit the transaction
                db.commit()
                db.refresh(record)

                # Log the successful status change
                log.info(f"Successfully updated order {order_id} status from {previous_status} to {form.status.value}")

                return PaymentOrderModel.model_validate(record)

            except HTTPException:
                # Re-raise HTTP exceptions (like 409 Conflict)
                db.rollback()
                raise
            except Exception as e:
                log.error(f"Error updating order {order_id} status: {e}")
                db.rollback()
                raise

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

    def get_all_orders(
            self, skip: int = 0, limit: int = 50,
            status: Optional[PaymentStatusEnum] = None,
            user_email: Optional[str] = None
    ) -> list[PaymentOrderWithUserModel]:
        """Get all orders across all users with optional filtering"""
        with get_db() as db:
            from open_webui.models.users import User

            query = (
                db.query(PaymentOrder, User)
                .join(User, PaymentOrder.user_id == User.id)
                .order_by(PaymentOrder.created_at.desc())
            )

            if status:
                query = query.filter(PaymentOrder.status == status)

            if user_email:
                query = query.filter(User.email.ilike(f"%{user_email}%"))

            rows = query.offset(skip).limit(limit).all()

            return [
                PaymentOrderWithUserModel(
                    **PaymentOrderModel.model_validate(order).model_dump(),
                    user_name=user.name,
                    user_email=user.email
                ) for order, user in rows
            ]


class PaymentOrderAuditTable:
    def create_audit_record(self, form: PaymentOrderAuditForm) -> Optional[PaymentOrderAuditModel]:
        """Create an audit record for a payment order action"""
        with get_db() as db:
            record = PaymentOrderAudit(
                id=str(uuid.uuid4()),
                order_id=form.order_id,
                action=form.action,
                actor_id=form.actor_id,
                actor_email=form.actor_email,
                actor_name=form.actor_name,
                previous_status=form.previous_status,
                new_status=form.new_status,
                reason=form.reason,
                audit_metadata=form.audit_metadata,
                created_at=int(time.time())
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return PaymentOrderAuditModel.model_validate(record) if record else None

    def get_audit_history(self, order_id: str) -> list[PaymentOrderAuditModel]:
        """Get audit history for a specific order"""
        with get_db() as db:
            records = (
                db.query(PaymentOrderAudit)
                .filter(PaymentOrderAudit.order_id == order_id)
                .order_by(PaymentOrderAudit.created_at.desc())
                .all()
            )
            return [PaymentOrderAuditModel.model_validate(record) for record in records]

    def get_audit_by_actor(self, actor_id: str, skip: int = 0, limit: int = 50) -> list[PaymentOrderAuditModel]:
        """Get audit records by actor (admin)"""
        with get_db() as db:
            records = (
                db.query(PaymentOrderAudit)
                .filter(PaymentOrderAudit.actor_id == actor_id)
                .order_by(PaymentOrderAudit.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [PaymentOrderAuditModel.model_validate(record) for record in records]

    def get_all_audit_records(self, skip: int = 0, limit: int = 50, action: Optional[str] = None) -> list[PaymentOrderAuditModel]:
        """Get all audit records with optional action filter"""
        with get_db() as db:
            query = db.query(PaymentOrderAudit).order_by(PaymentOrderAudit.created_at.desc())

            if action:
                query = query.filter(PaymentOrderAudit.action == action)

            records = query.offset(skip).limit(limit).all()
            return [PaymentOrderAuditModel.model_validate(record) for record in records]


# Instantiate tables for import
UserCredits = UserCreditsTable()
CreditTransactions = CreditTransactionsTable()
PaymentOrders = PaymentOrdersTable()
PaymentOrderAudits = PaymentOrderAuditTable()
