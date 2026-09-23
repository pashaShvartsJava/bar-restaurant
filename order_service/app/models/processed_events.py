from datetime import datetime, timezone

from sqlalchemy import Column, Integer, UUID, DateTime

from ..database.database import Base

class ProcessedEvent(Base):

    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
