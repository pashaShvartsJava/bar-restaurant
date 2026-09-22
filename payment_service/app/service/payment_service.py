from datetime import timezone, datetime

from .stripe_service import StripeService
from ..models.payments import PaymentStatus, Payment
from ..schemas.payment_schema import PaymentDTO
from ..repository.payment_repository import PaymentRepository
from uuid import UUID


class PaymentService:

    def __init__(self, payment_repository : PaymentRepository, stripe_service : StripeService):
        self.stripe_service = stripe_service
        self.payment_repository = payment_repository

    async def create_payment(self, data : PaymentDTO, client_id : UUID):
        payment = await self.payment_repository.create_payment(data, client_id)
        session = await self.stripe_service.create_checkout_session(payment)
        payment.stripe_session_id = session.id
        payment.stripe_payment_intent_id = session.payment_intent
        await self.payment_repository.save(payment)
        return payment, session.url

    async def handle_webhook(self, event) -> Payment | None:
        if event["type"] != "checkout.session.completed":
            return None
        session = event["data"]["object"]
        if session["payment_status"] != "paid":
            return None
        payment_id = session["metadata"]["payment_id"]
        payment = await self.payment_repository.get_by_id(int(payment_id))
        payment.stripe_session_id = session["id"]
        payment.stripe_payment_intent_id = session["payment_intent"]
        payment.status = PaymentStatus.PAID
        payment.updated_status = datetime.now(timezone.utc)
        payment = await self.payment_repository.save(payment)
        return payment