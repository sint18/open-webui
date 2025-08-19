import time
import uuid

from sqlalchemy import Column, String, Text, JSON, BigInteger

from open_webui.internal.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "affiliate"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(BigInteger, default=lambda: int(time.time()))
