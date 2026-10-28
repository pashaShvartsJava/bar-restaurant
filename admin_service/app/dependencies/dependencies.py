import httpx
from ..repository.admin_repository import AdminRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.admin_service import AdminService
from ..database.database import get_db
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings

INTERNAL_TOKEN=settings.internal_token

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return AdminService(AdminRepository(db))

def get_httpx_async_connection(request : Request) -> httpx.AsyncClient:
    return request.app.state.http_client

async def get_restaurant_dependency(slug : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"slug" : slug})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())