from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.outbox_payment_events import OutboxPaymentEvents
from uuid import UUID

from ..models.subscriptions import SubscriptionStatus


class OutboxPaymentEventsRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_event_by_event_id(self, event_id : str) -> OutboxPaymentEvents | None:
        result = await self.db.execute(select(OutboxPaymentEvents).where(OutboxPaymentEvents.event_id==event_id))
        return result.scalar_one_or_none()

    async def get_all_unpublished_events(self) -> List[OutboxPaymentEvents]:
        result = await self.db.execute(select(OutboxPaymentEvents).where(OutboxPaymentEvents.published_at==None))
        return result.scalars().all()

    async def mark_event_as_published(self, event : OutboxPaymentEvents):
        event.published_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def create_outbox_payment_event(self, payment_id : int, payment_order_id : int, payment_client_id : UUID, event_id : str) -> OutboxPaymentEvents:
        found_event = await self.get_event_by_event_id(event_id)
        if found_event is not None:
            return found_event
        outbox_event = OutboxPaymentEvents(
            event_type="PaymentPaid",
            payload={
                "payment_id": str(payment_id),
                "order_id": str(payment_order_id),
                "client_id": str(payment_client_id)
            },
            event_id=event_id
        )
        self.db.add(outbox_event)
        await self.db.flush()
        return outbox_event

    async def create_outbox_subscription_event(self,
                                               subscription_id : UUID,
                                               restaurant_id : UUID,
                                               owner_id : UUID,
                                               status : SubscriptionStatus,
                                               event_id : str) -> OutboxPaymentEvents:
        found_event = await self.get_event_by_event_id(event_id)
        if found_event is not None:
            return found_event
        outbox_event = OutboxPaymentEvents(
            event_type="SubscriptionStatusChanged",
            payload={
                "subscription_id": str(subscription_id),
                "restaurant_id": str(restaurant_id),
                "client_id": str(owner_id),
                "status": status.value
            },
            event_id=event_id
        )
        self.db.add(outbox_event)
        await self.db.flush()
        return outbox_event