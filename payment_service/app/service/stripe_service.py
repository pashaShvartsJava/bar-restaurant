from decimal import Decimal

import stripe

from ..config.config import settings


class StripeService:
    def __init__(self):
        self.client = stripe.StripeClient(settings.stripe_secret_key)

    async def create_checkout_session(self, payment):
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
                "success_url": "http://localhost:8080/payment/success",
                "cancel_url": "http://localhost:8080/payment/cancel"
            }
        )
        return session

    def construct_webhook_event(self, payload: bytes, signature: str):
        return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)