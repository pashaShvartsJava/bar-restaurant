import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .broker.rabbitmq import RabbitMQ
from .routes.routes import router as order_router
from .async_processes.async_processes import expire_order_loop
from .database.database import SessionLocal

rabbitmq = RabbitMQ()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    rabbit_task = asyncio.create_task(rabbitmq.consume())
    expire_task = asyncio.create_task(expire_order_loop(SessionLocal))
    try:
        yield
    finally:
        rabbit_task.cancel()
        expire_task.cancel()
        try:
            await rabbit_task
        except asyncio.CancelledError:
            pass
        try:
            await expire_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
app.include_router(order_router)