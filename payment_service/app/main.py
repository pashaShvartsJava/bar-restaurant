from fastapi import FastAPI

from .routes.routes import router as payment_router

app = FastAPI()

app.include_router(payment_router)