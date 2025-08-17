import enum
import time
import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Text,
    Boolean,
    Numeric,
    JSON,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
)

from open_webui.internal.db import Base


class AttrViaEnum(enum.Enum):
    """Method by which an attribution occurred."""

    link = "link"
    coupon = "coupon"
    manual = "manual"


class CommissionTypeEnum(enum.Enum):
    """Type of commission being awarded."""

    sale = "sale"
    lead = "lead"
    bonus = "bonus"


class CommissionStatusEnum(enum.Enum):
    """Lifecycle status of a commission."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"


class Application(Base):
    __tablename__ = "application"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()))


class Link(Base):
    __tablename__ = "link"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    url = Column(Text, nullable=False)
    created_at = Column(BigInteger, default=lambda: int(time.time()))


class Coupon(Base):
    __tablename__ = "coupon"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    discount_percent = Column(Numeric, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))


class Click(Base):
    __tablename__ = "click"
    __table_args__ = (
        {"schema": "affiliate", "postgresql_partition_by": "RANGE (created_at)"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    partner_id = Column(String, nullable=False)
    link_id = Column(String, nullable=True)
    coupon_id = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class Attribution(Base):
    __tablename__ = "attribution"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    click_id = Column(BigInteger, ForeignKey("affiliate.click.id"), nullable=False)
    partner_id = Column(String, nullable=False)
    attr_via = Column(
        SAEnum(AttrViaEnum, name="attr_via_enum", schema="affiliate"), nullable=False
    )
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class OrderAttribution(Base):
    __tablename__ = "order_attribution"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, nullable=False)
    attribution_id = Column(
        String, ForeignKey("affiliate.attribution.id"), nullable=False
    )
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class Commission(Base):
    __tablename__ = "commission"
    __table_args__ = (
        UniqueConstraint("order_id", "partner_id", "type", name="uq_commission_order_partner_type"),
        {"schema": "affiliate"},
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    order_id = Column(String, nullable=False)
    type = Column(
        SAEnum(CommissionTypeEnum, name="commission_type_enum", schema="affiliate"),
        nullable=False,
    )
    status = Column(
        SAEnum(CommissionStatusEnum, name="commission_status_enum", schema="affiliate"),
        nullable=False,
        default=CommissionStatusEnum.pending,
    )
    amount = Column(Numeric, nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class CommissionAdjustment(Base):
    __tablename__ = "commission_adjustment"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    commission_id = Column(
        String, ForeignKey("affiliate.commission.id"), nullable=False
    )
    amount = Column(Numeric, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class Payout(Base):
    __tablename__ = "payout"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    requested_amount = Column(Numeric, nullable=False)
    total_amount = Column(Numeric, nullable=False)
    fee_mmk = Column(Numeric, nullable=False, default=0)
    status = Column(String, nullable=False, default="pending")
    details = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class PayoutItem(Base):
    __tablename__ = "payout_item"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payout_id = Column(String, ForeignKey("affiliate.payout.id"), nullable=False)
    commission_id = Column(
        String, ForeignKey("affiliate.commission.id"), nullable=False
    )
    amount = Column(Numeric, nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class FraudFlag(Base):
    __tablename__ = "fraud_flag"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    flag_type = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))


class OutboxEvent(Base):
    __tablename__ = "outbox_event"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))
    processed_at = Column(BigInteger, nullable=True)
