from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.processed_events import ProcessedEvent


class ProcessedEventsRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def get_event_by_event_id(self, event_id : UUID) -> ProcessedEvent:
        result = await self.db.execute(select(ProcessedEvent).where(ProcessedEvent.event_id==event_id))
        return result.scalar_one_or_none()

    async def create_event(self, event_id : UUID) -> ProcessedEvent:
        new_event = ProcessedEvent(
            event_id=event_id
        )
        self.db.add(new_event)
        await self.db.flush()
        return new_event
