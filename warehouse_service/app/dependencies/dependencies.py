import httpx
from ..repository.product_repository import ProductRepository
from ..repository.reserved_products_repository import ReservedProductsRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO, RestaurantStatus
from ..schema.subscription_schema import SubscriptionDataDTO, PlanId
from ..service.product_service import ProductService
from ..database.database import get_db
from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings
from ..redis.redis_client import redis
from ..service.reserved_products_service import ReservedProductsService

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

def get_reserved_products_service_dependency(db : AsyncSession = Depends(get_db)):
    return ReservedProductsService(ReservedProductsRepository(db), ProductRepository(db))

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return ProductService(ProductRepository(db))

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

async def get_subscription_dependency(restaurant_id : str):
    client = await get_client()
    response = await client.get(url="http://payment-service:8008/subscription/get_subscription",
                                params={"restaurant_id": restaurant_id})
    return SubscriptionDataDTO(**response.json())

async def get_plan_in_cache(restaurant_id : str):
    plan_id = await redis.get(f"plan:{restaurant_id}")
    if plan_id is None:
        subscription = await get_subscription_dependency(restaurant_id)
        await redis.set(f"plan:{subscription.restaurant_id}", subscription.plan_id.value, ex=3600)
        plan_id = await redis.get(f"plan:{subscription.restaurant_id}")
    return plan_id

async def required_plans(current_plan_id : PlanId, *allowed_plans : PlanId):
    if current_plan_id not in allowed_plans:
        raise HTTPException(detail="Forbidden. This service is not available for this subscription plan", status_code=403)

async def verify_restaurant_status(status: RestaurantStatus):
    if status in (RestaurantStatus.CLOSED, RestaurantStatus.SUSPENDED):
        raise HTTPException(detail="Access temporarily restricted. If you are an owner then ask for help in FDCPlatform technical support.", status_code=403)

async def get_admin_data(restaurant_id : str, identity_id : str, token : str):
    client = await get_client()
    response = await client.get(url="http://admin-service:8002/admins/get_admin_data",
                                params={"restaurant_id": restaurant_id, "identity_id" : identity_id},
                                cookies={"access_token" : token})
    return response.json()