import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .broker.instance import rabbitmq
from .routes.routes import router as admin_router
from .async_processes.async_processes import outbox_publisher

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    producer_task = asyncio.create_task(outbox_publisher())
    try:
        yield
    finally:
        producer_task.cancel()
        try:
            await producer_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()
app = FastAPI(lifespan=lifespan)
app.include_router(admin_router)