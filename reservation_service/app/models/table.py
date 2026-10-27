import uuid

from sqlalchemy import Column, Integer, Enum as SQLEnum, UUID
from sqlalchemy.orm import relationship

from ..database.database import Base
from enum import Enum

class TableStatus(str, Enum):
    TAKEN = "taken"
    UNTAKEN = "untaken"

class Table(Base):

    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer, nullable=False, index=True, unique=True)
    status  = Column(SQLEnum(TableStatus), nullable=False, default=TableStatus.UNTAKEN)
    capacity = Column(Integer, nullable=False, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)

    table_sessions = relationship("TableSession", back_populates="table")
    reservations = relationship("Reservation", back_populates="table")

