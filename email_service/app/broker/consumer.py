import json
from uuid import UUID

from ..database.database import SessionLocal
from ..repository.email_repository import EmailRepository
from ..service.email_service import EmailService


class EmailVerificationConsumer:

    def __init__(self, queue):
        self.queue = queue

    async def consume(self):
        async with self.queue.iterator() as queue_iter:
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

class ChangePasswordVerificationConsumer:
    def __init__(self, queue):
        self.queue = queue

    async def consume(self):
        async with self.queue.iterator() as queue_iter:
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
                                    await email_service.send_change_password_verification(data["email"], data["token"])
                                else:
                                    print("THIS EVENT WAS ALREADY PROCESSED", flush=True)
                except Exception as e:
                    print("CONSUMER ERROR:", repr(e), flush=True)


class ChangeStatusConsumer:
    def __init__(self, queue):
        self.queue = queue

    async def consume(self):
        async with self.queue.iterator() as queue_iter:
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
                                    await email_service.send_change_status(data["client_id"],
                                                                           data["order_number"],
                                                                           data["order_status"],
                                                                           data["email"],
                                                                           data["order_items"],
                                                                           data["sum"])
                                else:
                                    print("THIS EVENT WAS ALREADY PROCESSED", flush=True)
                except Exception as e:
                    print("CONSUMER ERROR:", repr(e), flush=True)