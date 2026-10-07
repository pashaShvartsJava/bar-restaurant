import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.routes import router as email_router
from .broker.instance import rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer_email_task = asyncio.create_task(rabbitmq.consume_email_verification.consume())
    consumer_password_task = asyncio.create_task(rabbitmq.consume_change_password_verification.consume())
    consumer_change_status_task = asyncio.create_task(rabbitmq.change_status_queue.consume())
    consumer_reset_password_task = asyncio.create_task(rabbitmq.reset_password_queue.consume())
    try:
        yield
    finally:
        consumer_email_task.cancel()
        consumer_password_task.cancel()
        consumer_change_status_task.cancel()
        consumer_reset_password_task.cancel()
        try:
            await consumer_email_task
            await consumer_password_task
            await consumer_change_status_task
            await consumer_reset_password_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()

app = FastAPI(lifespan=lifespan)

app.include_router(email_router)