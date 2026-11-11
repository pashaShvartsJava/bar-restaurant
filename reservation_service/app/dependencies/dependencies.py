import httpx

from ..repository.table_repository import TableRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.table_service import TableService
from ..repository.reservation_repository import ReservationRepository
from ..service.reservation_service import ReservationService
from ..repository.table_session_repository import TableSessionRepository
from ..service.table_session_service import TableSessionService
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

def get_table_service_dependency(db : AsyncSession = Depends(get_db)):
    return TableService(TableRepository(db))

def get_table_session_service_dependency(db : AsyncSession = Depends(get_db)):
    return TableSessionService(TableSessionRepository(db), TableRepository(db))

def get_reservation_service_dependency(db : AsyncSession = Depends(get_db)):
    return ReservationService(ReservationRepository(db), TableRepository(db))

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