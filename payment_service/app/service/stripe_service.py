from decimal import Decimal

import stripe

from ..config.config import settings
from ..models.payments import Payment
from ..models.subscriptions import Subscription


class StripeService:
    def __init__(self):
        self.client = stripe.StripeClient(settings.stripe_secret_key)
        self.subscription_client = stripe.StripeClient(settings.stripe_secret_key_subscriptions)

    async def create_checkout_session(self, payment : Payment):
        session = await self.client.v1.checkout.sessions.create_async(
            params={
                "mode": "payment",
                "line_items": [
                    {
                        "price_data": {
                            "currency": "eur",
                            "product_data": {
                                "name": f"Order {payment.order_number}"
                            },
                            "unit_amount": int(payment.sum * Decimal("100"))
                        },
                        "quantity": 1
                    }
                ],
                "metadata": {
                    "payment_id": str(payment.id),
                    "order_id": str(payment.order_id)
                },
                "success_url": f"https://10.157.173.192:8443/payment/success?order_number={payment.order_number}",
                "cancel_url": "https://10.157.173.192:8443/payment/cancel"
            }, options={"idempotency_key" : f"payment:{payment.id}"}
        )
        return session

    def construct_webhook_event(self, payload: bytes, signature: str):
        return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)

    async def create_checkout_subscription_session(self, subscription: Subscription, key : str):
        session = await self.subscription_client.v1.checkout.sessions.create_async(
            params={
                "mode": "subscription",
                "line_items": [
                    {
                        "price_data": {
                            "currency": subscription.currency.lower(),
                            "product_data": {
                                "name": f"Plan {subscription.plan_name or subscription.plan_id}"
                            },
                            "unit_amount": int(subscription.price * Decimal("100")),
                            "recurring": {
                                "interval": "month" if subscription.billing_period == "monthly" else "year",
                            },
                        },
                        "quantity": 1,
                    }
                ],
                "metadata": {
                    "sub_idempotency_key": str(subscription.sub_idempotency_key),
                    "restaurant_id": str(subscription.restaurant_id),
                    "owner_id": str(subscription.owner_id),
                },
                "subscription_data": {
                    "trial_period_days": subscription.trial_days,
                    "metadata": {
                        "sub_idempotency_key": str(subscription.sub_idempotency_key),
                        "restaurant_id": str(subscription.restaurant_id),
                        "owner_id": str(subscription.owner_id),
                    },
                },
                "success_url": f"https://localhost:8443/payment/subscription/success?subscription_number={subscription.subscription_number}&key={key}",
                "cancel_url": "https://localhost:8443/payment/subscription/cancel",
            },
            options={"idempotency_key": f"subscription:{subscription.sub_idempotency_key}"},
        )
        return session

    def construct_webhook_subscription_event(self, payload: bytes, signature: str):
        return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret_subscriptions)