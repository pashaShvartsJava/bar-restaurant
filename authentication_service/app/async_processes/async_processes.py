import asyncio

from ..database.database import SessionLocal
from ..repositories.authentication_repository import AuthenticationRepository
from ..broker.producer import publish_email_verification, publish_change_password_verification


async def outbox_publisher():
    while True:
        async with SessionLocal() as session:
            repository = AuthenticationRepository(session)
            events = await repository.get_all_unpublished_events()
            for event in events:
                try:
                    if event.event_type == "EmailVerification":
                        await publish_email_verification(event.payload["email"], event.payload["token"], event.event_id)
                    if event.event_type == "ChangePasswordVerification":
                        await publish_change_password_verification(event.payload["email"], event.payload["token"], event.event_id)
                    await repository.mark_event_as_published(event)
                    await session.commit()
                except Exception:
                    await session.rollback()
        await asyncio.sleep(1)
