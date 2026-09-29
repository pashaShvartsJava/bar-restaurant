import asyncio
from contextlib import asynccontextmanager

from authx  import AuthXConfig

from fastapi import FastAPI

from .async_processes.async_processes import outbox_publisher
from .broker.instance import rabbitmq
from .routes.routes import router as auth_router
from .routes.admin_routes import router as router

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
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"

app.include_router(auth_router)
app.include_router(router)


