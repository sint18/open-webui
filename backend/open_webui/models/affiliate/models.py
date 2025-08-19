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
from sqlalchemy.orm import relationship

from open_webui.internal.db import Base
from open_webui.models.discount import DiscountCode


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
    review = "review"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"


class ApplicationStatusEnum(enum.Enum):
    """Status of a partner application."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class PartnerStatusEnum(enum.Enum):
    """Operational status of a partner."""

    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class PartnerTypeEnum(enum.Enum):
    """Classification type of partner."""

    individual = "individual"
    company = "company"


class PayoutStatusEnum(enum.Enum):
    """Lifecycle status of a payout."""

    pending = "pending"
    approved = "approved"
    paid = "paid"
    rejected = "rejected"


class AuditSeverityEnum(enum.Enum):
    """Severity level for audit logging."""

    info = "info"
    warning = "warning"
    critical = "critical"


class Application(Base):
    __tablename__ = "application"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    status = Column(
        SAEnum(ApplicationStatusEnum, name="application_status_enum", schema="affiliate"),
        nullable=False,
        default=ApplicationStatusEnum.pending,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()))


class PartnerProfile(Base):
    __tablename__ = "partner_profile"
    __table_args__ = {"schema": "affiliate"}

    partner_id = Column(String, ForeignKey("user.id"), primary_key=True)
    website = Column(Text, nullable=True)
    status = Column(
        SAEnum(PartnerStatusEnum, name="partner_status_enum", schema="affiliate"),
        nullable=False,
        default=PartnerStatusEnum.active,
    )
    type = Column(
        SAEnum(PartnerTypeEnum, name="partner_type_enum", schema="affiliate"),
        nullable=False,
        default=PartnerTypeEnum.individual,
    )
    payout_method = Column(String, nullable=True)
    payout_details = Column(Text, nullable=True)
    rates = Column(
        JSON,
        nullable=False,
        default=lambda: {"sales": 0.01, "clicks": 0.005},
    )
    terms = Column(JSON, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()))


class Link(Base):
    __tablename__ = "link"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    url = Column(Text, nullable=False)
    utm_source = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)
    utm_term = Column(String, nullable=True)
    utm_content = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))


class DiscountCodeBinding(Base):
    __tablename__ = "coupon"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=False)
    code = Column(String, ForeignKey("discount_code.code"), nullable=False, unique=True)
    expires_at = Column(BigInteger, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    discount_code = relationship("DiscountCode", backref="discount_code_bindings")


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
    lost_to_partner_id = Column(String, nullable=True)
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
    note = Column(Text, nullable=True)


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
    status = Column(
        SAEnum(PayoutStatusEnum, name="payout_status_enum", schema="affiliate"),
        nullable=False,
        default=PayoutStatusEnum.pending,
    )
    reference = Column(String, nullable=True, unique=True)
    details = Column(Text, nullable=True)
    approved_mmk = Column(Numeric, nullable=True)
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


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    severity = Column(
        SAEnum(AuditSeverityEnum, name="audit_severity_enum", schema="affiliate"),
        nullable=False,
    )
    details = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))
