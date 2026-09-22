import json
from uuid import UUID
import aio_pika
from aio_pika import connect_robust

from ..config.config import settings


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
        self.channel = await self.connection.channel()

        self.exchange = await self.channel.declare_exchange("payment_events",
                                                            aio_pika.ExchangeType.DIRECT,
                                                            durable=True)
        self.queue = await self.channel.declare_queue("order_payment", durable=True)
        await self.queue.bind(self.exchange, routing_key="payment_paid")

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def publish_payment_paid(self, payment_id: int, client_id: UUID):
        message = aio_pika.Message(
            body=json.dumps({
                "event": "payment_paid",
                "payment_id": payment_id,
                "client_id": str(client_id)})
            .encode(), content_type="application/json")
        await self.exchange.publish(message, routing_key="payment_paid")