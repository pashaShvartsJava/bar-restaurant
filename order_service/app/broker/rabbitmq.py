import json
from uuid import UUID

import aio_pika
from aio_pika import connect_robust
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config.config import settings
from ..models.orders import OrderStatus
from ..database.database import engine
from ..service.order_service import OrderService
from ..repository.order_repository import OrderRepository


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None

    async def connect(self):
        self.connection = await connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
        self.channel = await self.connection.channel()

        exchange = await self.channel.declare_exchange("payment_events",
                                                       aio_pika.ExchangeType.DIRECT,
                                                       durable=True)
        self.queue = await self.channel.declare_queue("order_payment", durable=True)
        await self.queue.bind(exchange, routing_key="payment_paid")

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def consume(self):
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    async with session_factory() as db:
                        repository = OrderRepository(db)
                        service = OrderService(repository)
                        await service.mark_order_as_paid(UUID(data["client_id"]), OrderStatus.PAID)