import json
import uuid
from uuid import UUID

from .rabbitmq import RabbitMQ
from ..database.database import SessionLocal
from ..repositories.restaurant_repository import RestaurantRepository
from ..repositories.processed_events_repository import ProcessedEventsRepository
import logging

logger = logging.getLogger(__name__)


class SubscriptionStatusChangedConsumer:

    def __init__(self, rabbitmq: RabbitMQ):
        self.rabbitmq = rabbitmq

    async def consume(self):
        async with self.rabbitmq.subscription_queue.iterator() as queue_iter:
            async for message in queue_iter:
                logger.info("CONSUMER: got message id=%s", message.message_id)
                try:
                    async with message.process():
                        data = json.loads(message.body)
                        try:
                            event_id = UUID(message.message_id)
                        except (ValueError, TypeError):
                            logger.warning("Invalid message_id: %s", message.message_id)
                            return
                        async with SessionLocal() as db:
                            async with db.begin():
                                event_repository = ProcessedEventsRepository(db)
                                restaurant_repository = RestaurantRepository(db)
                                event = await event_repository.get_event_by_event_id(event_id)
                                if event is None:
                                    logger.warning(f"SUBSCRIPTION EVENT: {data}")
                                    restaurant = await restaurant_repository.get_restaurant_by_id(uuid.UUID(data["restaurant_id"]))
                                    await restaurant_repository.change_restaurant_status(restaurant.id, data["status"])
                                    await event_repository.create_event(event_id)
                                else:
                                    logger.warning("THIS EVENT WAS ALREADY PROCESSED")
                except Exception as e:
                    logger.exception("Consumer error: %s", e)