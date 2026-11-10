import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database.database import SessionLocal
from .dependencies.dependencies import get_subscription_service_dependency
from .routes.payment_routes import router as payment_router
from .routes.subscription_routes import router as subscription_router
from .broker.instance import rabbitmq
from .async_processes.async_processes import outbox_publisher, vat_validity_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    outbox_task = asyncio.create_task(outbox_publisher())
    async with SessionLocal() as session:
        sub_service = get_subscription_service_dependency(session)
        vat_check_task = asyncio.create_task(vat_validity_scheduler(sub_service))
    try:
        yield
    finally:
        outbox_task.cancel()
        vat_check_task.cancel()
        try:
            await outbox_task
            await vat_check_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()


app = FastAPI(lifespan=lifespan)

app.include_router(payment_router)
app.include_router(subscription_router)