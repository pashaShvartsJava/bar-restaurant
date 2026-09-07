import uuid

from sqlalchemy import Column, Integer, String, Date, Enum as SQLEnum, UUID
from ..database.database import Base
from enum import Enum

class AdminRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"

class Status(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    FAILED = "failed"
    BLOCKED = "blocked"

class Admin(Base):

    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(UUID(as_uuid=True), unique=True, index=True,  default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    surname  = Column(String, index=True, nullable=False)
    birthday = Column(Date, index=True, nullable=False)
    phone = Column(String, index=True, nullable=False)
    role = Column(
        SQLEnum(AdminRole, name="role"),
        nullable=False,
        default=AdminRole.ADMIN
    )
    email = Column(String, nullable=False, index=True, unique=True)
