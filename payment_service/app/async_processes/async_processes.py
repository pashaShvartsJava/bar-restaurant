import asyncio

from ..database.database import SessionLocal
from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..broker.instance import rabbitmq


async def outbox_publisher():
    while True:
        async with SessionLocal() as session:
            repository = OutboxPaymentEventsRepository(session)
            events = await repository.get_all_unpublished_events()
            for event in events:
                try:
                    if event.event_type == "PaymentPaid":
                        await rabbitmq.publish_payment_paid(payment_id=event.payload["payment_id"],
                                                            client_id=event.payload["client_id"],
                                                            event_id=event.id)
                    await repository.mark_event_as_published(event.id)
                    await session.commit()
                except Exception:
                    await session.rollback()
        await asyncio.sleep(1)
