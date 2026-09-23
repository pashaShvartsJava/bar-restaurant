import aio_pika
from aio_pika import connect_robust
from ..config.config import settings


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
        self.channel = await self.connection.channel(publisher_confirms=True)

        exchange = await self.channel.declare_exchange("payment_events",
                                                       aio_pika.ExchangeType.DIRECT,
                                                       durable=True)
        self.queue = await self.channel.declare_queue("order_payment", durable=True)
        await self.queue.bind(exchange, routing_key="payment_paid")

    async def close(self):
        if self.connection:
            await self.connection.close()