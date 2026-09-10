from fastapi import FastAPI
from .models import Table, TableSession, Reservation
from .routes.routes import router as admin_router

app = FastAPI()

app.include_router(admin_router)