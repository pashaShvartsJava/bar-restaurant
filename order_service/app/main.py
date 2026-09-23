import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from .broker.consumer import OrderPaidConsumer
from .broker.rabbitmq import RabbitMQ
from .repository.processed_events_repository import ProcessedEventsRepository
from .routes.routes import router as order_router
from .async_processes.async_processes import expire_order_loop
from .database.database import SessionLocal
from .service.order_service import OrderService
from .repository.order_repository import OrderRepository
from sqlalchemy.ext.asyncio import AsyncSession

rabbitmq = RabbitMQ()
db = AsyncSession()
event_repository = ProcessedEventsRepository(db)
order_repository = OrderRepository(db)
order_service = OrderService(order_repository)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer = OrderPaidConsumer(rabbitmq=rabbitmq, order_service=order_service, event_repository=event_repository, db=db)
    expire_task = asyncio.create_task(expire_order_loop(SessionLocal))
    consumer_task = asyncio.create_task(consumer.consume())

    try:
        yield
    finally:
        consumer_task.cancel()
        expire_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        try:
            await expire_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
app.include_router(order_router)