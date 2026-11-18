import asyncio
import json
import os
from contextlib import asynccontextmanager
from contextvars import ContextVar

import httpx
from authx  import AuthXConfig

from fastapi import FastAPI, Request

from .async_processes.async_processes import outbox_publisher
from .broker.instance import rabbitmq
from .routes.routes import templates as auth_templates, router as auth_router
from .routes.admin_routes import templates as router_templates, router as router
from .routes.owner_routes import templates as owner_templates, router as owner_router
from .routes.super_admin_routes import router as super_admin_router
import logging


logging.basicConfig(level=logging.INFO)

LANG_DIR = "/authentication_service/lang"
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
auth_templates.env.globals["trans"] = trans
router_templates.env.globals["trans"] = trans
owner_templates.env.globals["trans"] = trans


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0), limits=httpx.Limits( max_connections=100,
                                                                                      max_keepalive_connections=20,
                                                                                      keepalive_expiry=30.0)) as client:
            app.state.http_client = client
            outbox_task = asyncio.create_task(outbox_publisher())
            try:
                yield
            finally:
                outbox_task.cancel()
                try:
                    await outbox_task
                except asyncio.CancelledError:
                    pass
    finally:
        await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"

app.include_router(auth_router)
app.include_router(router)
app.include_router(owner_router)
app.include_router(super_admin_router)

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


