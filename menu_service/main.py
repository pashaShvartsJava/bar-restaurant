from fastapi import FastAPI
from menu_service.routes.routes import router as admin_router
from menu_service.database import init_db

app = FastAPI()

init_db()

app.include_router(admin_router)