from sqlalchemy import Column, String, Enum as SQLEnum, Boolean
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid

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

class Identity(Base):

    __tablename__ = 'identity'

    id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4, index=True)
    email = Column(String, nullable=False, index=True, unique=True)
    password_hash = Column(String, nullable=False, index=True)
    role = Column(SQLEnum(IdentityRole), nullable=False, default=IdentityRole.USER)
    status = Column(SQLEnum(Status), nullable=False, default=Status.PENDING)
    verified_email = Column(Boolean, nullable=False, default=False)

    tokens = relationship("EmailVerificationToken",  back_populates="identity", cascade="all, delete-orphan")
    change_password_tokens = relationship("UpdatePasswordEmailToken", back_populates="identity", cascade="all, delete-orphan")
    reset_password_tokens = relationship("ResetPasswordToken", back_populates="identity", cascade="all, delete-orphan")
