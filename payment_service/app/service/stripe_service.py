from decimal import Decimal

import stripe

from ..config.config import settings
from ..models.payments import Payment


class StripeService:
    def __init__(self):
        self.client = stripe.StripeClient(settings.stripe_secret_key)

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