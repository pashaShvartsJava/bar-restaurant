import asyncio

from reservation_service.app.repository.reservation_repository import ReservationRepository
from ..database.database import SessionLocal
from ..broker.producer import publish_reservation_guest

async def outbox_publisher():
    while True:
        async with SessionLocal() as session:
            repository = ReservationRepository(session)
            events = await repository.get_all_unpublished_events()
            for event in events:
                try:
                    if event.event_type == "ReservationEvent":
                        await publish_reservation_guest(name=event.payload["name"],
                                                        surname=event.payload["surname"],
                                                        reservation_start=event.payload["reservation_start"],
                                                        email=event.payload["email"],
                                                        event_id=event.event_id)
                        await repository.mark_event_as_published(event)
                    await session.commit()
                except Exception:
                    await session.rollback()
        await asyncio.sleep(1)