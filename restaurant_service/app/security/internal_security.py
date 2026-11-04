from fastapi import HTTPException, Request
from ..config.config import settings

INTERNAL_TOKEN=settings.internal_token

async def verify_internal_token(internal_token : str):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(detail="Forbidden", status_code=403)

async def verify_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403)