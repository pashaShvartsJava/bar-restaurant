import httpx
from fastapi import Request

from ..repositories.authentication_repository import AuthenticationRepository
from ..services.authentication_service import AuthenticationService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return AuthenticationService(AuthenticationRepository(db))

def get_httpx_async_connection(request : Request) -> httpx.AsyncClient:
    return request.app.state.http_client