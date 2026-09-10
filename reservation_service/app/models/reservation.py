import uuid

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ..database.database import Base

class Reservation(Base):

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    reservation_number = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    reservation_start = Column(DateTime(timezone=True), nullable=False)
    reservation_end = Column(DateTime(timezone=True), nullable=False)

    table = relationship("Table", back_populates="reservations")