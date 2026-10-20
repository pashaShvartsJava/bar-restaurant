import httpx
from fastapi import Request

from ..repositories.restaurant_repository import RestaurantRepository
from ..services.restaurant_service import RestaurantService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_restaurant_dependency(db : AsyncSession = Depends(get_db)):
    return RestaurantService(RestaurantRepository(db))

def get_httpx_async_connection(request : Request) -> httpx.AsyncClient:
    return request.app.state.http_client