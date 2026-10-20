import asyncio
from contextlib import asynccontextmanager

import httpx
from authx  import AuthXConfig

from fastapi import FastAPI

from .async_processes.async_processes import outbox_publisher
from .broker.instance import rabbitmq
from .routes.routes import router as auth_router
from .routes.admin_routes import router as router
from .routes.owner_routes import router as owner_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0), limits=httpx.Limits( max_connections=100,
                                                                                      max_keepalive_connections=20,
                                                                                      keepalive_expiry=30.0)) as client:
            app.state.http_client = client
            outbox_task = asyncio.create_task(outbox_publisher())
            try:
                yield
            finally:
                outbox_task.cancel()
                try:
                    await outbox_task
                except asyncio.CancelledError:
                    pass
    finally:
        await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"

app.include_router(auth_router)
app.include_router(router)
app.include_router(owner_router)


