from authx  import AuthXConfig

from fastapi import FastAPI
from .routes.routes import router as auth_router

app = FastAPI()
config = AuthXConfig()

app.include_router(auth_router)