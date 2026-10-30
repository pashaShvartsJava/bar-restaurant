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

async def get_restaurant_dependency_by_id(restaurant_id : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_id",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"restaurant_id" : restaurant_id})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())

async def get_authentication_key(restaurant_id : str, token : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://authentication-service:8000/get_auth_key",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"restaurant_id" : restaurant_id},
                                    cookies={"access_token": token})
        response.raise_for_status()
    key = response.json()
    return key

async def get_new_key(restaurant_id : str, token : str):
    async with httpx.AsyncClient() as client:
        response = await client.post(url="http://authentication-service:8000/generate_auth_key",
                                     headers={"internal_token": INTERNAL_TOKEN},
                                     params={"restaurant_id": restaurant_id},
                                     cookies={"access_token": token})
        response.raise_for_status()
    new_key = response.json()
    return new_key