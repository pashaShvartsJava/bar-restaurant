import asyncio

from ..database.database import SessionLocal
from ..repository.order_repository import OrderRepository
from ..service.order_service import OrderService
from ..repository.guest_repository import GuestRepository
from ..broker.producer import publish_change_status


async def expire_order_loop(session_factory):
    try:
        while True:
            async with session_factory() as db:
                guest_repository = GuestRepository(db)
                repository = OrderRepository(db)
                service = OrderService(repository, guest_repository)
                await service.mark_order_as_expired()
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        raise

async def outbox_publisher():
    while True:
        async with SessionLocal() as session:
            repository = OrderRepository(session)
            events = await repository.get_all_unpublished_events()
            for event in events:
                try:
                    if event.event_type == "ChangeOrderStatus":
                        await publish_change_status(client_id=event.payload["client_id"],
                                                    order_number=event.payload["order_number"],
                                                    order_status=event.payload["order_status"],
                                                    email=event.payload["email"],
                                                    order_items=event.payload["order_items"],
                                                    sum=event.payload["sum"],
                                                    event_id=event.event_id)
                        await repository.mark_event_as_published(event)
                    await session.commit()
                except Exception:
                    await session.rollback()
        await asyncio.sleep(1)
