import asyncio

from ..database.database import SessionLocal
from ..repository.outbox_repository import OutboxPaymentEventsRepository
import logging
from ..broker.producers import publish_subscription_event, publish_payment_paid

logger = logging.getLogger(__name__)


async def outbox_publisher():
    while True:
        async with SessionLocal() as session:
            repository = OutboxPaymentEventsRepository(session)
            events = await repository.get_all_unpublished_events()
            for event in events:
                try:
                    if event.event_type == "PaymentPaid":
                        await publish_payment_paid(payment_id=event.payload["payment_id"],
                                                            client_id=event.payload["client_id"],
                                                            event_id=event.id,
                                                            order_id=event.payload["order_id"])
                    if event.event_type == "SubscriptionStatusChanged":
                        await publish_subscription_event(subscription_id=event.payload["subscription_id"],
                                                                  restaurant_id=event.payload["restaurant_id"],
                                                                  client_id=event.payload["client_id"],
                                                                  status=event.payload["status"],
                                                                  event_id=event.id)
                    await repository.mark_event_as_published(event)
                    await session.commit()
                except KeyError:
                    logger.exception("Malformed payload for event %s: %s", event.id, event.payload)
                    await repository.mark_event_as_published(event)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logger.exception("Failed to publish outbox event %s", event.id)
        await asyncio.sleep(1)
