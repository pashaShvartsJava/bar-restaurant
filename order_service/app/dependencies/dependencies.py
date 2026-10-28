import httpx

from ..repository.order_repository import OrderRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.order_service import OrderService
from ..repository.guest_repository import GuestRepository

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings

INTERNAL_TOKEN=settings.internal_token

def get_order_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = OrderRepository(db)
    guest_repository = GuestRepository(db)
    return OrderService(menu_repository, guest_repository)

async def get_restaurant_dependency(slug : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"slug" : slug})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())