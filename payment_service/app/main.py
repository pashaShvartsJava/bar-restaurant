import asyncio
import json
import os
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request

from .database.database import SessionLocal
from .dependencies.dependencies import get_subscription_service_dependency
from .routes.payment_routes import templates as payment_templates,  router as payment_router
from .routes.subscription_routes import templates as subscription_templates, router as subscription_router
from .routes.super_admin_routes import router as super_admin_router
from .broker.instance import rabbitmq
from .async_processes.async_processes import outbox_publisher, vat_validity_scheduler



LANG_DIR = "/payment_service/lang"
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
payment_templates.env.globals["trans"] = trans
subscription_templates.env.globals["trans"] = trans


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    outbox_task = asyncio.create_task(outbox_publisher())
    async with SessionLocal() as session:
        sub_service = get_subscription_service_dependency(session)
        vat_check_task = asyncio.create_task(vat_validity_scheduler(sub_service))
    try:
        yield
    finally:
        outbox_task.cancel()
        vat_check_task.cancel()
        try:
            await outbox_task
            await vat_check_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()


app = FastAPI(lifespan=lifespan)

app.include_router(payment_router)
app.include_router(subscription_router)
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