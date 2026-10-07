import asyncio
import aio_pika
from aio_pika import connect_robust

from ..config.config import settings


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.email_verification_queue = None
        self.change_password_verification_queue = None
        self.reset_password_queue = None

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

        self.exchange = await self.channel.declare_exchange("email_verification_event",
                                                            aio_pika.ExchangeType.DIRECT,
                                                            durable=True)
        self.email_verification_queue = await self.channel.declare_queue(
            "email_verification", durable=True)
        await self.email_verification_queue.bind(
            self.exchange, routing_key="email_verification_event")

        self.change_password_verification_queue = await self.channel.declare_queue(
     "change_password_verification", durable=True)
        await self.change_password_verification_queue.bind(
            self.exchange, routing_key="change_password_verification_event")

        self.reset_password_queue = await self.channel.declare_queue("reset_password", durable=True)
        await self.reset_password_queue.bind(self.exchange, routing_key="reset_password_event")

    async def close(self):
        if self.connection:
            await self.connection.close()
