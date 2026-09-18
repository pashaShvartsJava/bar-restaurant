import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum


from ..database.database import Base

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED_ADDRESS = "confirmed_address"
    PAID = "paid"
    PREPARING = "prepared"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED_BEFORE = "cancelled_before"
    CANCELLED_AFTER = "cancelled_after"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(UUID(as_uuid=True), index=True, nullable=False, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_status = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    sum = Column(DECIMAL(10, 2), nullable=False, index=True)
    address_id = Column(Integer, ForeignKey("delivery_addresses.id"), nullable=True)

    order_items = relationship("OrderItem", back_populates="order")
    address = relationship("DeliveryAddress", back_populates="order")
