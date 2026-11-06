import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

import stripe

from ..config.config import settings
from ..models.payments import Payment
from ..models.subscriptions import Subscription

def create_line_items(total_food : Decimal, total_drink : Decimal) -> list[dict]:
    FOOD_TAX_RATE_ID = "txr_1UYsLHEBszTkRGCJ6l2dQU2p"
    DRINK_TAX_RATE_ID = "txr_1UYsLWEBszTkRGCJwpsVY8nG"
    line_items = []
    if total_food > 0:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Food"},
                "unit_amount": int(total_food * Decimal("100")),
            },
            "quantity": 1,
            "tax_rates": [FOOD_TAX_RATE_ID]})
    if total_drink > 0:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Drinks"},
                "unit_amount": int(total_drink * Decimal("100")),
            },
            "quantity": 1,
            "tax_rates": [DRINK_TAX_RATE_ID]})
    return line_items


class StripeService:
    def __init__(self):
        self.client = stripe.StripeClient(settings.stripe_secret_key_subscriptions)

    async def create_checkout_session(self, payment : Payment, stripe_account_id : str, order_commission_percent : int):
        application_fee_eur = (
                payment.sum * (Decimal(order_commission_percent) / Decimal("100"))
                + (payment.sum + Decimal("0.25")) / Decimal("0.985")
                - payment.sum
        )
        application_fee = int((application_fee_eur * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        line_items = create_line_items(payment.food_total, payment.drink_total)
        params = {
            "mode": "payment",
            "line_items": line_items,
            "metadata": {
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
            },
            "payment_intent_data": {
                "application_fee_amount": application_fee,
                "transfer_data": {"destination": stripe_account_id},
                "on_behalf_of": stripe_account_id,
            },
            "success_url": f"https://localhost:8443/payment/success?order_number={payment.order_number}",
            "cancel_url": "https://localhost:8443/payment/cancel"}
        params_hash = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()[:16]
        session = await self.client.v1.checkout.sessions.create_async(params=params,
                                                                      options={"idempotency_key": f"payment:{payment.id}:{params_hash}"})
        return session

    def construct_webhook_event(self, payload: bytes, signature: str):
        return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret_subscriptions)

    async def create_checkout_subscription_session(self, subscription: Subscription, key : str):
        session = await self.client.v1.checkout.sessions.create_async(
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