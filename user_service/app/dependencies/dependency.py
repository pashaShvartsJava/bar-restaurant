import httpx

from ..repositories.user_repository import UserRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..services.user_service import UserService
from ..repositories.address_repository import AddressRepository
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings

INTERNAL_TOKEN = settings.internal_token

client_connection: httpx.AsyncClient | None = None

async def get_client() -> httpx.AsyncClient:
    global client_connection
    if client_connection is None:
        client_connection = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            headers={"internal_token": INTERNAL_TOKEN},
        )
    return client_connection

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return UserService(UserRepository(db), AddressRepository(db))

async def get_restaurant_dependency(slug : str):
    client = await get_client()
    response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    params={"slug" : slug})
    return RestaurantConstructorDTO(**response.json())