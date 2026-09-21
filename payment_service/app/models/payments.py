from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, UUID, Enum as SQLEnum, DECIMAL, DateTime
from enum import Enum

from ..database.database import Base

class PaymentStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Payment(Base):

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id  = Column(Integer, unique=True, nullable=False)
    order_number = Column(UUID(as_uuid=True), index=True, nullable=False)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED)
    sum = Column(DECIMAL(10, 2), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_status = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    stripe_session_id = Column(String, nullable=True, unique=True)
    stripe_payment_intent_id = Column(String, nullable=True, unique=True)