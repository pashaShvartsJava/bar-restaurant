import httpx

from ..repository.menu_repository import MenuRepository
from ..repository.category_repository import CategoryRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO, CURRENCY_SYMBOLS
from ..service.dish_service import MenuService
from ..service.category_service import CategoryService
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


def get_menu_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = MenuRepository(db)
    return MenuService(menu_repository)

def get_category_service_dependency(db: AsyncSession = Depends(get_db)):
    category_repository = CategoryRepository(db)
    return CategoryService(category_repository)

async def get_restaurant_dependency(slug : str):
    client = await get_client()
    response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                params={"slug" : slug})
    return RestaurantConstructorDTO(**response.json())

async def get_restaurant_dependency_by_id(restaurant_id : str):
    client = await get_client()
    response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_id",
                                params={"restaurant_id" : restaurant_id})
    return RestaurantConstructorDTO(**response.json())

def get_currency_symbol(code: str | None) -> str:
    if not code:
        return ""
    key = code.strip().upper()
    return CURRENCY_SYMBOLS.get(key, key)