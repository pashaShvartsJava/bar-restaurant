from datetime import datetime, timezone

from sqlalchemy import Column, String, Enum as SQLEnum, Integer, Date, DateTime, ForeignKey
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base

class IdentityRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class Status(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    FAILED = "failed"
    BLOCKED = "blocked"

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(UUID, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    surname = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    birthday = Column(Date, nullable=False, index=True)
    phone = Column(String, nullable=False)
    role = Column(SQLEnum(IdentityRole), nullable=False, index=True)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda : datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    address = relationship("Address", back_populates="users")