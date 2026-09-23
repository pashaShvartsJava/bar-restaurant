import asyncio
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
        while True:
            try:
                self.connection = await connect_robust(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    login=settings.RABBITMQ_USER,
                    password=settings.RABBITMQ_PASSWORD
                )
                break
            except Exception as e:
                print(f"RabbitMQ unavailable: {e}. Retry in 5 seconds...")
                await asyncio.sleep(5)
        self.channel = await self.connection.channel(publisher_confirms=True)

        self.exchange = await self.channel.declare_exchange("payment_events",
                                                            aio_pika.ExchangeType.DIRECT,
                                                            durable=True)

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def publish_payment_paid(self, payment_id: int, client_id: UUID, event_id : UUID):
        message = aio_pika.Message(
            body=json.dumps({
                "event": "payment_paid",
                "payment_id": payment_id,
                "client_id": str(client_id)})
            .encode(), message_id=str(event_id), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
        await self.exchange.publish(message, routing_key="payment_paid")