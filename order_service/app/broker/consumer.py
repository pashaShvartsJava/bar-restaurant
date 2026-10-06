import json
from uuid import UUID

from .rabbitmq import RabbitMQ
from ..database.database import SessionLocal
from ..models.orders import OrderStatus
from ..repository.guest_repository import GuestRepository
from ..repository.processed_events_repository import ProcessedEventsRepository
from ..repository.order_repository import OrderRepository
from ..service.order_service import OrderService


class OrderPaidConsumer:

    def __init__(self, rabbitmq: RabbitMQ):
        self.rabbitmq = rabbitmq

    async def consume(self):
        async with self.rabbitmq.queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process():
                        data = json.loads(message.body)
                        event_id = UUID(message.message_id)
                        async with SessionLocal() as db:
                            async with db.begin():
                                event_repository = ProcessedEventsRepository(db)
                                order_repository = OrderRepository(db)
                                guest_repository = GuestRepository(db)
                                order_service = OrderService(order_repository, guest_repository)
                                event = await event_repository.get_event_by_event_id(event_id)
                                if event is None:
                                    print(f"PAYMENT EVENT: {data}", flush=True)

                                    order = await order_service.get_order_by_id(int(data["order_id"]))
                                    print(
                                        f"ORDER BEFORE: {order.id if order else None}, STATUS: {order.status if order else None}",
                                        flush=True)

                                    await order_service.mark_order_as_paid(order.id, OrderStatus.PAID)
                                    print("ORDER STATUS SET TO PAID", flush=True)

                                    await event_repository.create_event(event_id)
                                    print("PROCESSED EVENT CREATED", flush=True)

                                    email = await order_service.get_customer_email(UUID(data["client_id"]))
                                    print(f"CUSTOMER EMAIL: {email}", flush=True)

                                    await order_repository.create_outbox_change_status_event(email=email, order=order)
                                    print("EMAIL OUTBOX CREATED", flush=True)
                                else:
                                    print("THIS EVENT WAS ALREADY PROCESSED", flush=True)

                except Exception as e:
                    print("CONSUMER ERROR:", repr(e), flush=True)