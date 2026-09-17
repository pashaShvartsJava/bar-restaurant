from fastapi import FastAPI
from .routes.routes import router as order_router

app = FastAPI()
app.include_router(order_router)