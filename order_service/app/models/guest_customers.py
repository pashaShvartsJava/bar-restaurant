import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, DECIMAL, Enum as SQLEnum, Date
from sqlalchemy.orm import relationship
from enum import Enum


from ..database.database import Base


class GuestCustomer(Base):

    __tablename__ = "guest_customers"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(UUID(as_uuid=True), unique=True, nullable=False,  index=True)
    name = Column(String, nullable=False, index=True)
    surname = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False)
    birthday = Column(Date, nullable=False, index=True)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))