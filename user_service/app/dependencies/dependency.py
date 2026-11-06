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

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return UserService(UserRepository(db), AddressRepository(db))

async def get_restaurant_dependency(slug : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"slug" : slug})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())