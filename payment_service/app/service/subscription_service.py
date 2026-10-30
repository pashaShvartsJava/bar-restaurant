import asyncio
import uuid
from datetime import timezone, datetime

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from .stripe_service import StripeService
from ..broker.rabbitmq import RabbitMQ
from ..models.subscriptions import Subscription, SubscriptionStatus
from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..repository.subscription_repository import SubscriptionRepository
from uuid import UUID
from ..schemas.subscription_schema import SubscriptionCheckoutDTO
import logging
logger = logging.getLogger(__name__)


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

    async def get_subscription_by_owner_id(self, customer_id: UUID, restaurant_id: UUID) -> Subscription:
        return await self.subscription_repository.get_subscription_by_owner_id(customer_id, restaurant_id)

    async def create_subscription(self, data : SubscriptionCheckoutDTO):
        subscription = await self.subscription_repository.create_subscription(data)
        session = await self.stripe_service.create_checkout_subscription_session(subscription)
        subscription.stripe_checkout_session_id = session.id
        await self.subscription_repository.save_subscription(subscription)
        return subscription, session.url

    async def delete_saga_subscription(self, sub_idempotency_key: str):
        return await self.subscription_repository.delete_saga_subscription(sub_idempotency_key)

    async def handle_subscription_webhook(self, event) -> Subscription | None:
        session = event["data"]["object"].to_dict()
        print(f"WH: payment_status={session.get('payment_status')}", flush=True)
        if session.get("payment_status") not in ("paid", "no_payment_required"):
            print("WH: EXIT at payment_status", flush=True)
            return None
        sub_idempotency_key = session.get("metadata", {}).get("sub_idempotency_key")
        print(f"WH: idempotency_key={sub_idempotency_key!r}", flush=True)
        if not sub_idempotency_key:
            print("WH: EXIT at idempotency_key", flush=True)
            return None
        session_id = session.get("id")
        print(f"WH: session_id={session_id!r}", flush=True)
        if not session_id:
            print("WH: EXIT at session_id", flush=True)
            return None
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        print(f"WH: raw customer={customer_id!r} sub={subscription_id!r}", flush=True)
        if not customer_id or not subscription_id:
            try:
                fresh_session = await asyncio.to_thread(
                    stripe.checkout.Session.retrieve, session_id)
                customer_id = customer_id or fresh_session.customer
                subscription_id = subscription_id or fresh_session.subscription
                print(f"WH: after retrieve customer={customer_id!r} sub={subscription_id!r}", flush=True)
            except stripe.error.StripeError as e:
                print(f"WH: EXIT at retrieve error: {e}", flush=True)
                return None
        if not customer_id or not subscription_id:
            print("WH: EXIT at still empty after retrieve", flush=True)
            return None
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_idempotency_key(uuid.UUID(sub_idempotency_key))
            if subscription is None:
                print(f"WH: EXIT at subscription not found for key={sub_idempotency_key}", flush=True)
                return None
            print(f"WH: BEFORE assign id={subscription.id} "
                 f"customer={subscription.stripe_customer_id!r} "
                 f"sub={subscription.stripe_subscription_id!r}", flush=True)
            subscription.stripe_customer_id = customer_id
            subscription.stripe_subscription_id = subscription_id
            subscription.stripe_checkout_session_id = session_id
            print(f"WH: AFTER assign customer={subscription.stripe_customer_id!r} "
                 f"sub={subscription.stripe_subscription_id!r}", flush=True)
        return subscription

    async def handle_subscription_updated(self, event):
        stripe_subscription = event["data"]["object"].to_dict()
        stripe_subscription_id = stripe_subscription["id"]
        if not stripe_subscription_id:
            return None
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if subscription is None:
                metadata = stripe_subscription.get("metadata", {}) or {}
                sub_key = metadata.get("sub_idempotency_key")
                if sub_key:
                    subscription = await self.subscription_repository.get_by_idempotency_key(uuid.UUID(sub_key))
            if subscription is None:
                return None
            old_status = subscription.status
            try:
                new_status = SubscriptionStatus(stripe_subscription["status"])
            except ValueError:
                print("Unknown subscription status from Stripe: %s", stripe_subscription["status"])
                return None
            items = stripe_subscription["items"]["data"] if "items" in stripe_subscription else []
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
            subscription.status = new_status
            if new_status != old_status:
                await self.outbox_repository.create_outbox_subscription_event(
                    subscription.id,
                    subscription.restaurant_id,
                    subscription.owner_id,
                    new_status,
                    event["id"]
                )
        return subscription

    async def handle_subscription_deleted(self, event):
        stripe_subscription = event["data"]["object"]
        async with self.db.begin():
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription["id"])
            if subscription is None:
                return None
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.canceled_at = datetime.now(timezone.utc)
            await self.outbox_repository.create_outbox_subscription_event(subscription.id,
                                                                          subscription.restaurant_id,
                                                                          subscription.owner_id,
                                                                          subscription.status,
                                                                          event["id"])
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

