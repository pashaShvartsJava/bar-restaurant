import uuid

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum


from ..database.database import Base

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PREPARING = "prepared"
    DELIVERING = "delivering"
    COMPLETED = "completed"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(UUID(as_uuid=True), index=True, nullable=False, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_status = Column(DateTime(timezone=True), nullable=False)
    sum = Column(DECIMAL(10, 2), nullable=False, index=True)

    order_items = relationship("OrderItem", back_populates="order")