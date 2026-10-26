from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from .routes.routes import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0), limits=httpx.Limits( max_connections=100,
                                                                                   max_keepalive_connections=20,
                                                                                      keepalive_expiry=30.0)) as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(admin_router)

