import asyncio

import aio_pika
from aio_pika import connect_robust
from ..config.config import settings


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.add_product_queue = None

    async def connect(self):
        while True:
            try:
                self.connection = await connect_robust(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    login=settings.RABBITMQ_USER,
                    password=settings.RABBITMQ_PASSWORD)
                break
            except Exception as e:
                print(f"RabbitMQ unavailable: {e}. Retry in 5 seconds...")
                await asyncio.sleep(5)
        self.channel = await self.connection.channel(publisher_confirms=True)

        self.exchange = await self.channel.declare_exchange("product_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
        self.add_product_queue = await self.channel.declare_queue("add_product_queue", durable=True)
        await self.add_product_queue.bind(self.exchange, routing_key="add_product_routing_key")


    async def close(self):
        if self.connection:
            await self.connection.close()