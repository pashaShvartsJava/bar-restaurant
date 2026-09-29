import json
from uuid import UUID
from ..database.database import SessionLocal
from .rabbitmq import RabbitMQ
from ..repository.email_repository import EmailRepository
from ..service.email_service import EmailService


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
                            email_repository = EmailRepository(db)
                            email_service = EmailService(email_repository)
                            async with db.begin():
                                event = await email_repository.get_event_by_event_id(event_id)
                                if event is None:
                                    await email_repository.create_event(event_id)
                                    await email_service.send_verification_email(data["email"], data["token"])
                                else:
                                    print("THIS EVENT WAS ALREADY PROCESSED", flush=True)
                except Exception as e:
                    print("CONSUMER ERROR:", repr(e), flush=True)