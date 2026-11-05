import httpx

from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..repository.payment_repository import PaymentRepository
from ..repository.subscription_repository import SubscriptionRepository
from ..schemas.restaurant_schema import RestaurantConstructorDTO, CURRENCY_SYMBOLS
from ..service.payment_service import PaymentService

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.stripe_service import StripeService
from ..broker.instance import rabbitmq
from ..service.subscription_service import SubscriptionService
from ..config.config import settings

INTERNAL_TOKEN=settings.internal_token

def get_payment_service_dependency(db: AsyncSession = Depends(get_db)):
    return PaymentService(db, PaymentRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db))

def get_subscription_service_dependency(db: AsyncSession = Depends(get_db)):
    return SubscriptionService(db, SubscriptionRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db))

async def get_restaurant_dependency_by_id(restaurant_id : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_id",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"restaurant_id" : restaurant_id})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())

def get_currency_symbol(code: str | None) -> str:
    if not code:
        return ""
    key = code.strip().upper()
    return CURRENCY_SYMBOLS.get(key, key)

async def save_restaurant_dependency(data : RestaurantConstructorDTO):
    async with httpx.AsyncClient() as client:
        response = await client.patch(url="http://restaurant-service:8010/restaurants/save_restaurant_webhook",
                                      headers={"internal_token" : INTERNAL_TOKEN},
                                      params={"stripe_charges_enabled" : data.stripe_charges_enabled,
                                              "stripe_payouts_enabled" : data.stripe_payouts_enabled,
                                              "restaurant_id" : data.id})
        response.raise_for_status()

async def get_restaurant_dependency_by_stripe_account_id(stripe_account_id : str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_stripe_account_id",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"stripe_account_id" : stripe_account_id})
        response.raise_for_status()
    return RestaurantConstructorDTO(**response.json())