import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .broker.consumers import SubscriptionStatusChangedConsumer
from .broker.instance import rabbitmq
from .routes.routes import router as router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer = SubscriptionStatusChangedConsumer(rabbitmq)
    consumer_task = asyncio.create_task(consumer.consume())
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()
app = FastAPI(lifespan=lifespan)
app.include_router(router)