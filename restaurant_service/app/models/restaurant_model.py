from sqlalchemy import Column, DateTime, String, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql  import UUID
from enum import Enum

from sqlalchemy.orm import relationship

from ..database.database import Base

class RestaurantStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class Restaurant(Base):

    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    timezone = Column(String, nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    status =Column(SQLEnum(RestaurantStatus, name="restaurant_status"), nullable=False, default=RestaurantStatus.PENDING)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),)

    memberships = relationship("RestaurantMembership", back_populates="restaurant", cascade="all, delete-orphan")