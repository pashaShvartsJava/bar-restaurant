import asyncio
import aio_pika
from aio_pika import connect_robust

from .consumer import EmailVerificationConsumer, ChangePasswordVerificationConsumer, ChangeStatusConsumer, ResetPasswordConsumer
from ..config.config import settings


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.email_verification_queue = None
        self.change_password_verification_queue = None
        self.consume_email_verification = None
        self.consume_change_password_verification = None
        self.change_status_queue = None
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
        self.consume_email_verification = EmailVerificationConsumer(self.email_verification_queue)

        self.change_password_verification_queue = await self.channel.declare_queue(
            "change_password_verification", durable=True)
        await self.change_password_verification_queue.bind(
            self.exchange, routing_key="change_password_verification_event")
        self.consume_change_password_verification = ChangePasswordVerificationConsumer(self.change_password_verification_queue)

        self.change_status_queue = await self.channel.declare_queue("change_status", durable=True)
        await self.change_status_queue.bind(self.exchange, routing_key="change_status_event")
        self.change_status_queue = ChangeStatusConsumer(self.change_status_queue)

        self.reset_password_queue = await self.channel.declare_queue("reset_password", durable=True)
        await self.reset_password_queue.bind(self.exchange, routing_key="reset_password_event")
        self.reset_password_queue = ResetPasswordConsumer(self.reset_password_queue)

    async def close(self):
        if self.connection:
            await self.connection.close()