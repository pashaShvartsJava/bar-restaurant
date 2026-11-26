import json
import uuid
from uuid import UUID
from ..database.database import SessionLocal
from ..broker.rabbitmq import RabbitMQ
from ..repository.processed_events_repository import ProcessedEventsRepository
from ..repository.product_repository import ProductRepository


class AddProductConsumer:

    def __init__(self, rabbitmq: RabbitMQ):
        self.rabbitmq = rabbitmq

    async def consume(self):
        async with self.rabbitmq.add_product_queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process():
                        data = json.loads(message.body)
                        event_id = UUID(message.message_id)
                        async with SessionLocal() as db:
                            async with db.begin():
                                event_repository = ProcessedEventsRepository(db)
                                product_repository = ProductRepository(db)
                                event = await event_repository.get_event_by_event_id(event_id)
                                if event is None:
                                    print(f"PRODUCT EVENT: {data}", flush=True)

                                    product = await product_repository.create_product(data["name"],
                                                                                      data["unit"],
                                                                                      data["restaurant_id"],
                                                                                      data["product_id"])
                                    print(f"PRODUCT BEFORE: {product.id if product else None}", flush=True)

                                    await event_repository.create_event(event_id)
                                    print("PROCESSED EVENT CREATED", flush=True)
                                else:
                                    print("THIS EVENT WAS ALREADY PROCESSED", flush=True)

                except Exception as e:
                    print("CONSUMER ERROR:", repr(e), flush=True)