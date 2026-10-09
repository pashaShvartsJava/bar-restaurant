import asyncio

import aio_pika
from aio_pika import connect_robust
from ..config.config import settings


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.create_reservation_queue = None

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

        self.exchange = await self.channel.declare_exchange("reservation_events_events",
                                                       aio_pika.ExchangeType.DIRECT,
                                                       durable=True)
        self.create_reservation_queue = await self.channel.declare_queue("create_reservation", durable=True)
        await self.create_reservation_queue.bind(self.exchange, routing_key="create_reservation")

    async def close(self):
        if self.connection:
            await self.connection.close()