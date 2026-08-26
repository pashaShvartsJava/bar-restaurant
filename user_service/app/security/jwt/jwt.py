import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError
from starlette.requests import Request

import os

PUBLIC_SECRET_KEY = os.getenv("JWT_PUBLIC_KEY_PATH")
ALGORITHM = os.getenv("JWT_ALGORITHM")

def decode_access_token(token : str) -> dict:
    try:
        payload = jwt.decode(token, PUBLIC_SECRET_KEY, ALGORITHM)
        return payload
    except InvalidTokenError:
        raise ValueError("Authentication required")

def get_payload(request : Request):
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    return decode_access_token(token)