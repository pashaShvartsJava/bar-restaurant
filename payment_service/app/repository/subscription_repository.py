import secrets
import string
import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from ..models.subscriptions import Subscription, SubscriptionStatus, VatStatus
from ..schemas.subscription_schema import SubscriptionCheckoutDTO, PLANS, PlanId


def generate_subscription_number() -> str:
    alphabet = string.ascii_uppercase + string.digits  # без похожих символов: 0/O, 1/I
    alphabet = alphabet.replace("0", "").replace("O", "").replace("1", "").replace("I", "")
    code = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"SUB-{code}"

class SubscriptionRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_restaurant_percentage_commission(self, restaurant_id : UUID) -> Subscription:
        result = await self.db.execute(select(Subscription)
                                       .where(Subscription.restaurant_id == restaurant_id)
                                       .where(or_(Subscription.status==SubscriptionStatus.ACTIVE,
                                                  Subscription.status==SubscriptionStatus.TRIALING)))
        return result.scalar_one_or_none()

    async def get_subscription_by_owner_id(self, customer_id : UUID, restaurant_id : UUID) -> Subscription:
        result = await self.db.execute(select(Subscription)
                                       .where(Subscription.owner_id==customer_id,
                                              Subscription.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_subscription_by_restaurant_id(self, restaurant_id: UUID) -> Subscription:
        result = await self.db.execute(select(Subscription)
                                       .where(Subscription.restaurant_id == restaurant_id)
                                       .where(or_(Subscription.status==SubscriptionStatus.ACTIVE,
                                                  Subscription.status==SubscriptionStatus.TRIALING)))
        return result.scalar_one_or_none()

    async def get_subscriptions_with_valid_vats(self) -> list[Subscription]:
        result = await self.db.execute(select(Subscription).where(Subscription.vat_status==VatStatus.VALID)
                                                     .where(or_(Subscription.status == SubscriptionStatus.ACTIVE,
                                                                Subscription.status == SubscriptionStatus.TRIALING)))
        return result.scalars().all()

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
            sub_idempotency_key=data.sub_idempotency_key,
            vat_id=data.vat_id,
            vat_status=data.vat_verified,
            vat_checked_at=data.vat_checked_at,
            country=data.country
        )
        self.db.add(new_subscription)
        await self.db.flush()
        return new_subscription

    async def save_subscription(self, subscription : Subscription):
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def get_by_idempotency_key(self, key : UUID):
        result = await self.db.execute(select(Subscription)
                                       .where(Subscription.sub_idempotency_key==key)
                                       .where(or_(Subscription.status == SubscriptionStatus.ACTIVE,
                                                  Subscription.status == SubscriptionStatus.TRIALING))
                                       )
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(self, stripe_subscription_id : str) -> Subscription:
        result = await self.db.execute(select(Subscription)
                                       .where(Subscription.stripe_subscription_id==stripe_subscription_id)
                                       .where(or_(Subscription.status == SubscriptionStatus.ACTIVE,
                                                  Subscription.status == SubscriptionStatus.TRIALING))
                                       )
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, stripe_customer_id : str) -> Subscription:
        result = await self.db.execute(select(Subscription)
                                       .where(Subscription.stripe_customer_id == stripe_customer_id)
                                       .where(or_(Subscription.status == SubscriptionStatus.ACTIVE,
                                                  Subscription.status == SubscriptionStatus.TRIALING))
                                       )
        return result.scalar_one_or_none()

    async def update(self, subscription : Subscription):
        await self.db.flush()
        await self.db.refresh(subscription)

    async def delete_saga_subscription(self, sub_idempotency_key : str):
        found_subscription = await self.get_by_idempotency_key(uuid.UUID(sub_idempotency_key))
        await self.db.delete(found_subscription)
        await self.db.commit()