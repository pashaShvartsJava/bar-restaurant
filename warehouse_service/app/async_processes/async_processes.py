import asyncio

from ..database.database import SessionLocal
from ..repository.product_repository import ProductRepository
from ..broker.producers import publish_add_product_event

async def outbox_publisher():
    while True:
        async with SessionLocal() as session:
            repository = ProductRepository(session)
            events = await repository.get_all_unpublished_events()
            for event in events:
                try:
                    if event.event_type == "AddProductEvent":
                        await publish_add_product_event(name=event.payload["name"],
                                                        unit=event.payload["unit"],
                                                        restaurant_id=event.payload["restaurant_id"],
                                                        product_id=event.payload["product_id"],
                                                        event_id=event.event_id)
                        await repository.mark_event_as_published(event)
                    await session.commit()
                except Exception:
                    await session.rollback()
        await asyncio.sleep(1)