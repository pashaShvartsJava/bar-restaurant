import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database.database import Base

class DeliveryAddress(Base):

    __tablename__ = "delivery_addresses"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id") , nullable=False)
    city = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    street = Column(String, nullable=False)
    house = Column(Integer, nullable=False)
    apartment = Column(Integer)

    order = relationship("Order", back_populates="address_id")


