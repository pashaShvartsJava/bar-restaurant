import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.routes import router as order_router
from .async_processes.async_processes import expire_order_loop
from .database.database import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(expire_order_loop(SessionLocal))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)
app.include_router(order_router)