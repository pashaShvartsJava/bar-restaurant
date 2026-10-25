import httpx

from ..repository.admin_repository import AdminRepository
from ..service.admin_service import AdminService
from ..database.database import get_db
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return AdminService(AdminRepository(db))

def get_httpx_async_connection(request : Request) -> httpx.AsyncClient:
    return request.app.state.http_client