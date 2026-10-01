import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .broker.consumer import OrderPaidConsumer
from .routes.routes import router as order_router
from .async_processes.async_processes import expire_order_loop, outbox_publisher
from .database.database import SessionLocal
from .broker.instance import rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer = OrderPaidConsumer(rabbitmq)
    consumer_task = asyncio.create_task(consumer.consume())
    expire_task = asyncio.create_task(expire_order_loop(SessionLocal))
    producer_task = asyncio.create_task(outbox_publisher())
    try:
        yield
    finally:
        consumer_task.cancel()
        expire_task.cancel()
        producer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        try:
            await expire_task
        except asyncio.CancelledError:
            pass
        try:
            await producer_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()
app = FastAPI(lifespan=lifespan)
app.include_router(order_router)