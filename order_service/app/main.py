import asyncio
import json
import os
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request

from .broker.consumer import OrderPaidConsumer
from .routes.routes import templates as order_templates, router as order_router
from .routes.analytics_routes import templates as analytics_templates, router as analytics_router
from .async_processes.async_processes import expire_order_loop, outbox_publisher
from .database.database import SessionLocal
from .broker.instance import rabbitmq


LANG_DIR = "/order_service/lang"
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
order_templates.env.globals["trans"] = trans
analytics_templates.env.globals["trans"] = trans


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    consumer = OrderPaidConsumer(rabbitmq)
    consumer_task = asyncio.create_task(consumer.consume())
    expire_task = asyncio.create_task(expire_order_loop(SessionLocal))
    producer_task = asyncio.create_task(outbox_publisher())
    try:
        yield
    finally:
        consumer_task.cancel()
        expire_task.cancel()
        producer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        try:
            await expire_task
        except asyncio.CancelledError:
            pass
        try:
            await producer_task
        except asyncio.CancelledError:
            pass
        await rabbitmq.close()
app = FastAPI(lifespan=lifespan)
app.include_router(order_router)
app.include_router(analytics_router)

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