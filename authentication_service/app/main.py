from authx  import AuthXConfig

from fastapi import FastAPI
from .routes.routes import router as auth_router
from .routes.admin_routes import router as router

app = FastAPI()
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"

app.include_router(auth_router)
app.include_router(router)


