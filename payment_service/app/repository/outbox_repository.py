from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.outbox_payment_events import OutboxPaymentEvents
from ..models.payments import Payment
from ..schemas.payment_schema import PaymentDTO
from uuid import UUID

class OutboxPaymentEventsRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_all_unpublished_events(self) -> List[OutboxPaymentEvents]:
        result = await self.db.execute(select(OutboxPaymentEvents).where(OutboxPaymentEvents.published_at==None))
        return result.scalars().all()

    async def mark_event_as_published(self, event : OutboxPaymentEvents):
        event.published_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(event)

    async def create_outbox_event(self, payment_id : int, payMent_order_id : UUID, payment_client_id : UUID) -> OutboxPaymentEvents:
        outbox_event = OutboxPaymentEvents(
            event_type="PaymentPaid",
            payload={
                "payment_id": str(payment_id),
                "order_id": str(payMent_order_id),
                "client_id": str(payment_client_id)
            }
        )
        self.db.add(outbox_event)
        await self.db.commit()
        await self.db.refresh(outbox_event)
        return outbox_event