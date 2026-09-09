from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes.routes import router as admin_router

app = FastAPI()

app.include_router(admin_router)
app.mount(
    "/media",
    StaticFiles(directory="app/templates_menu/media"),
    name="media"
)
