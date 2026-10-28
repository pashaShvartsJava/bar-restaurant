import httpx

from ..repository.menu_repository import MenuRepository
from ..repository.category_repository import CategoryRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.dish_service import MenuService
from ..service.category_service import CategoryService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings

INTERNAL_TOKEN = settings.internal_token


def get_menu_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = MenuRepository(db)
    return MenuService(menu_repository)

def get_category_service_dependency(db: AsyncSession = Depends(get_db)):
    category_repository = CategoryRepository(db)
    return CategoryService(category_repository)

async def get_restaurant_dependency(slug : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"slug" : slug})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())