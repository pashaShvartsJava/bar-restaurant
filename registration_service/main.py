from fastapi import FastAPI
from registration_service.routes.routes import router as registration_router

app = FastAPI
app.include_router(registration_router)