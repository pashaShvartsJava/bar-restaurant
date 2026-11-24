from fastapi import HTTPException
from ..config.config import settings

INTERNAL_TOKEN=settings.internal_token

async def verify_internal_token(internal_token : str):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(detail="Forbidden", status_code=403)