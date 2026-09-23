import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .rabbitmq import RabbitMQ
from ..models.orders import OrderStatus
from ..repository.processed_events_repository import ProcessedEventsRepository
from ..service.order_service import OrderService



class OrderPaidConsumer:

    def __init__(self, db : AsyncSession,
                 rabbitmq : RabbitMQ,
                 order_service : OrderService,
                 event_repository : ProcessedEventsRepository):
        self.db = db
        self.rabbitmq = rabbitmq
        self.order_service = order_service
        self.event_repository = event_repository

    async def consume(self):
        async with self.rabbitmq.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    event_id = UUID(message.message_id)
                    async with self.db.begin():
                        event = await self.event_repository.get_event_by_event_id(event_id)
                        if event is None:
                            await self.order_service.mark_order_as_paid(UUID(data["client_id"]), OrderStatus.PAID)
                            await self.event_repository.create_event(event_id)
                        else:
                            print("THIS EVENT WAS ALREADY PROCESSED")