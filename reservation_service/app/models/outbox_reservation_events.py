import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, UUID, DateTime, func

from sqlalchemy.dialects.postgresql import JSONB

from ..database.database import Base

class OutboxReservationEvent(Base):

    __tablename__ = "outbox_reservation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),)
    published_at = Column(DateTime(timezone=True), nullable=True)
    event_id = Column(String, nullable=True, unique=True)