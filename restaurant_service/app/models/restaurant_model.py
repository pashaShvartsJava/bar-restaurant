import uuid

from sqlalchemy import Column, DateTime, String, Enum as SQLEnum, func, Text, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True, index=True)

    country = Column(String, nullable=False)
    city = Column(String, nullable=False, index=True)
    address = Column(String, nullable=False)

    timezone = Column(String, nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    status = Column(SQLEnum(RestaurantStatus, name="restaurant_status"), nullable=False, default=RestaurantStatus.PENDING, index=True)
    slogan = Column(String(120), nullable=True)
    tagline = Column(String(160), nullable=True)
    short_description = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    about_title = Column(String(120), nullable=True)
    photo_url = Column(String(500), nullable=True)

    phone = Column(String(32), nullable=True)
    email = Column(String(254), nullable=True)
    instagram_url = Column(String(500), nullable=True)

    working_hours = Column(JSONB, nullable=True)

    accepts_reservations = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    accepts_delivery = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    accepts_orders_on_site = Column(Boolean, nullable=False, default=True, server_default=text("true"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    memberships = relationship("RestaurantMembership", back_populates="restaurant", cascade="all, delete-orphan")