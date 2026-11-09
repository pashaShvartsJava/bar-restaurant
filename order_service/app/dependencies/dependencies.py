from uuid import UUID

import httpx
from httpx import HTTPStatusError

from ..repository.order_repository import OrderRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.order_service import OrderService
from ..repository.guest_repository import GuestRepository

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings
import logging

logger = logging.getLogger(__name__)

INTERNAL_TOKEN=settings.internal_token
client_connection: httpx.AsyncClient | None = None

async def get_client() -> httpx.AsyncClient:
    global client_connection
    if client_connection is None:
        client_connection = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            headers={"internal_token": INTERNAL_TOKEN},
        )
    return client_connection

def get_order_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = OrderRepository(db)
    guest_repository = GuestRepository(db)
    return OrderService(menu_repository, guest_repository)

async def get_restaurant_dependency(slug : str):
    client = await get_client()
    try:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    params={"slug" : slug})
    except HTTPStatusError as exc:
        logger.error("restaurant-service вернул %s: %s",exc.response.status_code, exc.response.text)
        raise
    return RestaurantConstructorDTO(**response.json())

async def get_restaurant_percentage_commission(restaurant_id : UUID):
    client = await get_client()
    try:
        response = await client.get(url="http://payment-service:8008/subscription/get_percentage_commission",
                                params={"restaurant_id" : str(restaurant_id)})
    except HTTPStatusError as exc:
        logger.error("restaurant-service вернул %s: %s",exc.response.status_code, exc.response.text)
        raise
    return response.json()