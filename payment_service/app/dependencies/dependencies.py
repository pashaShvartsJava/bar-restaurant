import httpx

from ..models.subscriptions import PlanId
from ..redis.redis_client import redis
from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..repository.payment_repository import PaymentRepository
from ..repository.subscription_repository import SubscriptionRepository
from ..schemas.restaurant_schema import RestaurantConstructorDTO, CURRENCY_SYMBOLS
from ..schemas.subscription_schema import SubscriptionDataDTO
from ..service.payment_service import PaymentService

from ..database.database import get_db
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.stripe_service import StripeService
from ..broker.instance import rabbitmq
from ..service.subscription_service import SubscriptionService
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

def get_payment_service_dependency(db: AsyncSession = Depends(get_db)):
    return PaymentService(db, PaymentRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db), SubscriptionRepository(db))

def get_subscription_service_dependency(db: AsyncSession = Depends(get_db)):
    return SubscriptionService(db, SubscriptionRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db))

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

async def save_restaurant_dependency(data : RestaurantConstructorDTO):
    client = await get_client()
    await client.patch(url="http://restaurant-service:8010/restaurants/save_restaurant_webhook",
                                      params={"stripe_charges_enabled" : data.stripe_charges_enabled,
                                              "stripe_payouts_enabled" : data.stripe_payouts_enabled,
                                              "restaurant_id" : data.id})

async def get_restaurant_dependency_by_stripe_account_id(stripe_account_id : str):
    client = await get_client()
    response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_stripe_account_id",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"stripe_account_id" : stripe_account_id})
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