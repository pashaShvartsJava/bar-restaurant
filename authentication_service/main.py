from authx  import AuthX, AuthXConfig

from fastapi import FastAPI
from routes.routes import router as auth_router

app = FastAPI()
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"

app.include_router(auth_router)


