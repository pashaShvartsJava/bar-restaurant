import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .broker.consumer import consume
from .routes.routes import router as email_router
from .broker.instance import rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer_task = asyncio.create_task(consume.consume())
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()

app = FastAPI()

app.include_router(email_router)