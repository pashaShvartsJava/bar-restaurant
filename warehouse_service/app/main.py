import asyncio
import json
import os
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request, HTTPException
from starlette.responses import RedirectResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from .async_processes.async_processes import outbox_publisher
from .broker.instance import rabbitmq
from .routes.routes import templates, router as warehouse_router

LANG_DIR = "/warehouse_service/lang"
_current_lang = ContextVar("current_lang", default="en")
_translations = {}



def load_translations():
    global _translations
    if not os.path.exists(LANG_DIR):
        print(f"WARNING: LANG_DIR not found: {LANG_DIR}")
        return
    for lang_code in os.listdir(LANG_DIR):
        lang_path = os.path.join(LANG_DIR, lang_code)
        if os.path.isdir(lang_path):
            file_path = os.path.join(lang_path, "messages.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    _translations[lang_code] = json.load(f)

def trans(key: str, **kwargs) -> str:
    lang = _current_lang.get()
    text = _translations.get(lang, {}).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text

load_translations()
templates.env.globals["trans"] = trans


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    producer_task = asyncio.create_task(outbox_publisher())
    try:
        yield
    finally:
        producer_task.cancel()
        try:
            await producer_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
app.include_router(warehouse_router)
app.mount("/media", StaticFiles(directory="app/templates/media"), name="media")

@app.middleware("http")
async def language_middleware(request: Request, call_next):
    lang = request.cookies.get("user_lang")
    if not lang:
        accept = request.headers.get("Accept-Language", "en")
        lang = accept.split(",")[0].split("-")[0]
    if lang not in ("en", "de", "ru", "uk", "fr", "ka"):
        lang = "en"
    _current_lang.set(lang)
    return await call_next(request)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        login_url = (exc.headers or {}).get("X-Auth-Redirect", "/login")
        response = RedirectResponse(url=login_url, status_code=303)
        response.delete_cookie(key="access_token", path="/")
        return response
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)