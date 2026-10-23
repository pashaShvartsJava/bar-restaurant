import secrets
import string
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from ..models.subscriptions import Subscription
from ..schemas.subscription_schema import SubscriptionCheckoutDTO, PLANS, PlanId


def generate_subscription_number() -> str:
    alphabet = string.ascii_uppercase + string.digits  # без похожих символов: 0/O, 1/I
    alphabet = alphabet.replace("0", "").replace("O", "").replace("1", "").replace("I", "")
    code = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"SUB-{code}"

class SubscriptionRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def create_subscription(self, data : SubscriptionCheckoutDTO) -> Subscription:
        subscription_number = generate_subscription_number()
        plan_name = PLANS.get(PlanId(data.plan_id))
        new_subscription = Subscription(
            subscription_number=subscription_number,
            restaurant_id=data.restaurant_id,
            email=data.email,
            owner_id=data.user_id,
            plan_id=data.plan_id,
            plan_name=plan_name["name"],
            billing_period=data.billing_period,
            trial_days=data.trial_days,
            price=data.price,
            order_commission_percent=data.order_commission_percent,
            currency=data.currency,
            sub_idempotency_key=data.sub_idempotency_key
        )
        self.db.add(new_subscription)
        await self.db.flush()
        return new_subscription

    async def save_subscription(self, subscription : Subscription):
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def get_by_idempotency_key(self, key : UUID):
        result = await self.db.execute(select(Subscription).where(Subscription.sub_idempotency_key==key))
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(self, stripe_subscription_id : str) -> Subscription:
        result = await self.db.execute(select(Subscription).where(Subscription.stripe_subscription_id==stripe_subscription_id))
        return result.scalar_one_or_none()

    async def delete_saga_subscription(self, sub_idempotency_key : str):
        found_subscription = await self.get_by_idempotency_key(uuid.UUID(sub_idempotency_key))
        await self.db.delete(found_subscription)
        await self.db.commit()