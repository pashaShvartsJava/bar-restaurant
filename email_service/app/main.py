from fastapi import FastAPI

from .routes.routes import router as email_router

app = FastAPI()

app.include_router(email_router)