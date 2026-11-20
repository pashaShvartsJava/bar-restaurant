import httpx
from fastapi import Request, HTTPException

from ..models.restaurant_model import RestaurantStatus
from ..redis.redis_client import redis
from ..repositories.restaurant_repository import RestaurantRepository
from ..schema.subscription_schema import SubscriptionDataDTO
from ..services.restaurant_service import RestaurantService
from ..database.database import get_db
from fastapi import Depends
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

def get_restaurant_dependency(db : AsyncSession = Depends(get_db)):
    return RestaurantService(RestaurantRepository(db))

def get_httpx_async_connection(request : Request) -> httpx.AsyncClient:
    return request.app.state.http_client

async def verify_restaurant_status(status: RestaurantStatus):
    if status in (RestaurantStatus.CLOSED, RestaurantStatus.SUSPENDED):
        raise HTTPException(detail="Access temporarily restricted. If you are an owner then ask for help in FDCPlatform technical support.", status_code=403)

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