from pathlib import Path

import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError, PyJWTError
from starlette.requests import Request
from starlette.responses import RedirectResponse

from ...config.config import settings

PUBLIC_SECRET_KEY = Path(settings.jwt_public_key_path).read_text()
PLATFORM_ADMIN_JWT_SECRET = settings.PLATFORM_ADMIN_JWT_SECRET
ALGORITHM = settings.jwt_algorithm

def decode_access_token(token : str) -> dict:
    try:
        payload = jwt.decode(token, PUBLIC_SECRET_KEY,  algorithms=ALGORITHM)
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401,detail="Authentication required")

def get_payload(request: Request, login_url: str = "/login"):
    token = request.cookies.get("access_token")
    if not token:
        response = RedirectResponse(url=login_url, status_code=303)
        response.delete_cookie(key="access_token", path="/")
        raise HTTPException(status_code=401, detail="Authorization required", headers={"X-Auth-Redirect": login_url})
    try:
        payload = decode_access_token(token)
        return payload
    except (PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"X-Auth-Redirect": login_url})

def decode_secret_access_token(token : str) -> dict:
    try:
        payload = jwt.decode(token, PLATFORM_ADMIN_JWT_SECRET,  algorithms="HS256")
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401,detail="Authentication required")

def get_secret_payload(request : Request):
    token = request.cookies.get("access_token")
    if not token:
        response = RedirectResponse(url="/admin/login/secret_api", status_code=303)
        response.delete_cookie(key="access_token", path="/")
        raise HTTPException( status_code=401, detail="Authorization required",
                             headers={"X-Auth-Redirect": "/admin/login/secret_api"})
    try:
        payload = decode_secret_access_token(token)
        return payload
    except (PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token",
                            headers={"X-Auth-Redirect": "/admin/login/secret_api"})