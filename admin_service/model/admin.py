from sqlalchemy import Column, Integer, String, Date, Enum as SQLEnum
from ..database import Base
from enum import Enum

class AdminRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"

class Admin(Base):

    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    surname  = Column(String, index=True, nullable=False)
    birthday = Column(Date, index=True, nullable=False)
    phone = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    password = Column(String, nullable=False, unique=True)
    role = Column(
        SQLEnum(AdminRole),
        nullable=False,
        default=AdminRole.ADMIN
    )
