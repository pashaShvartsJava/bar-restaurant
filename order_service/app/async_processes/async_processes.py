import asyncio

from ..repository.order_repository import OrderRepository
from ..service.order_service import OrderService


async def expire_order_loop(session_factory):
    try:
        while True:
            async with session_factory() as db:
                repository = OrderRepository(db)
                service = OrderService(repository)
                await service.mark_order_as_expired()
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        raise
