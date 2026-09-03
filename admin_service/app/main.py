from fastapi import FastAPI
from admin_service.app.routes import router as admin_router

app = FastAPI()

app.include_router(admin_router)

