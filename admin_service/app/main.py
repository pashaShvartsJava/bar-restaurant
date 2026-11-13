import json
import os
from contextlib import asynccontextmanager
from contextvars import ContextVar

import httpx
from fastapi import FastAPI, Request

from .routes.routes import templates, router as admin_router

LANG_DIR = "/admin_service/lang"
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
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0),
                                 limits=httpx.Limits(max_connections=100,
                                                     max_keepalive_connections=20,
                                                     keepalive_expiry=30.0)) as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(admin_router)

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

