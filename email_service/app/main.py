import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.routes import router as email_router
from .broker.instance import rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer_task = asyncio.create_task(rabbitmq.consume.consume())
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

app.include_router(email_router)