import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError
from starlette.requests import Request

from authentication_service.authentication_service.config.config import settings
from authentication_service.authentication_service.model.identity_model import IdentityRole

PUBLIC_SECRET_KEY = settings.jwt_public_key_path
ALGORITHM = settings.jwt_algorithm

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