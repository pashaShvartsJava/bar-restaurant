import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.routes import router as payment_router
from .broker.instance import rabbitmq
from .async_processes.async_processes import outbox_publisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    outbox_task = asyncio.create_task(outbox_publisher())
    try:
        yield
    finally:
        outbox_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()


app = FastAPI(lifespan=lifespan)

app.include_router(payment_router)