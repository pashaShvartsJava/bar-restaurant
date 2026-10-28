from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, UUID
from sqlalchemy.orm import relationship

from ..database.database import Base

class TableSession(Base):

    __tablename__ = "table_sessions"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    session_start = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),)
    session_end = Column(DateTime(timezone=True), default=None)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)

    table = relationship("Table", back_populates="table_sessions")