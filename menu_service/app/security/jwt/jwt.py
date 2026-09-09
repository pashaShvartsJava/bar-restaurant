from pathlib import Path

import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError
from starlette.requests import Request
from ...config.config import settings

PUBLIC_SECRET_KEY = Path(settings.jwt_public_key_path).read_text()
ALGORITHM = settings.jwt_algorithm

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            PUBLIC_SECRET_KEY,
            algorithms=ALGORITHM
        )
        return payload

    except InvalidTokenError as e:
        print("JWT ERROR:", type(e).__name__, str(e))

        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

def get_payload(request : Request):
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=403, detail="Authorization required")
    return decode_access_token(token)