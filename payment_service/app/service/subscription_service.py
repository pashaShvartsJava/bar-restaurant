import uuid
from datetime import timezone, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .stripe_service import StripeService
from ..broker.rabbitmq import RabbitMQ
from ..models.subscriptions import Subscription, SubscriptionStatus
from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..repository.subscription_repository import SubscriptionRepository
from uuid import UUID
from ..schemas.subscription_schema import SubscriptionCheckoutDTO


class SubscriptionService:

    def __init__(self,
                 db : AsyncSession,
                 subscription_repository : SubscriptionRepository,
                 stripe_service : StripeService,
                 rabbitmq : RabbitMQ,
                 outbox_repository : OutboxPaymentEventsRepository):

        self.db = db
        self.stripe_service = stripe_service
        self.subscription_repository = subscription_repository
        self.rabbitmq = rabbitmq
        self.outbox_repository = outbox_repository

    async def create_subscription(self, data : SubscriptionCheckoutDTO, restaurant_id : UUID):
        subscription = await self.subscription_repository.create_subscription(restaurant_id, data)
        session = await self.stripe_service.create_checkout_subscription_session(subscription)
        subscription.stripe_checkout_session_id = session.id
        await self.subscription_repository.save_subscription(subscription)
        return subscription, session.url

    async def handle_subscription_webhook(self, event) -> Subscription | None:
        session = event["data"]["object"]
        if session.get("payment_status") not in ("paid", "no_payment_required"):
            return None
        sub_idempotency_key = session.get("metadata", {}).get("sub_idempotency_key")
        if not sub_idempotency_key:
            return None
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_idempotency_key(uuid.UUID(sub_idempotency_key))
            if subscription is None:
                return None
            if subscription.stripe_subscription_id == session.get("subscription"):
                return subscription
            subscription.stripe_customer_id = session.get("customer")
            subscription.stripe_subscription_id = session.get("subscription")
            subscription.stripe_checkout_session_id = session.get("id")
        return subscription

    async def handle_subscription_updated(self, event):
        stripe_subscription = event["data"]["object"]
        stripe_subscription_id = stripe_subscription.get("id")
        if not stripe_subscription_id:
            return None
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if subscription is None:
                return None
            subscription.status = SubscriptionStatus(stripe_subscription["status"])
            items = stripe_subscription.get("items", {}).get("data", [])
            if items:
                subscription.current_period_start = datetime.fromtimestamp(items[0]["current_period_start"], tz=timezone.utc)
                subscription.current_period_end = datetime.fromtimestamp(items[0]["current_period_end"], tz=timezone.utc)
            subscription.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)
            if stripe_subscription.get("canceled_at"):
                subscription.canceled_at = datetime.fromtimestamp(stripe_subscription["canceled_at"], tz=timezone.utc)
            if stripe_subscription.get("trial_start"):
                subscription.trial_start = datetime.fromtimestamp(stripe_subscription["trial_start"], tz=timezone.utc)
            if stripe_subscription.get("trial_end"):
                subscription.trial_end = datetime.fromtimestamp(stripe_subscription["trial_end"], tz=timezone.utc)
        return subscription

    async def handle_subscription_deleted(self, event):
        stripe_subscription = event["data"]["object"]
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription["id"])
            if subscription is None:
                return None
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.canceled_at = datetime.now(timezone.utc)
        return subscription

    async def handle_invoice_payment_failed(self, event):
        invoice = event["data"]["object"]
        stripe_subscription_id = invoice.get("subscription")
        if not stripe_subscription_id:
            return None
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if subscription is None:
                return None
            error = invoice.get("last_payment_error") or {}
            subscription.last_payment_error = error.get("message")
        return subscription

