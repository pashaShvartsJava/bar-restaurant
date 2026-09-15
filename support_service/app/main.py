from fastapi import FastAPI
from .routes.user_routes import router as user_router
from .routes.admin_routes import router as admin_router

app = FastAPI()
app.include_router(user_router)
app.include_router(admin_router)
