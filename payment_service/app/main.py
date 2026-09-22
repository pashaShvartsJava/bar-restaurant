from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes.routes import router as payment_router
from .broker.instance import rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    yield
    await rabbitmq.close()


app = FastAPI(lifespan=lifespan)

app.include_router(payment_router)