import httpx
from ..repository.admin_repository import AdminRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.admin_service import AdminService
from ..database.database import get_db
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings

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

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return AdminService(AdminRepository(db))

def get_httpx_async_connection(request : Request) -> httpx.AsyncClient:
    return request.app.state.http_client

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

async def get_authentication_key(restaurant_id : str, token : str):
    client = await get_client()
    response = await client.get(url="http://authentication-service:8000/get_auth_key",
                                params={"restaurant_id" : restaurant_id},
                                cookies={"access_token": token})
    key = response.json()
    return key

async def get_new_key(restaurant_id : str, token : str):
    client = await get_client()
    response = await client.post(url="http://authentication-service:8000/generate_auth_key",
                                 params={"restaurant_id": restaurant_id},
                                 cookies={"access_token": token})
    new_key = response.json()
    return new_key