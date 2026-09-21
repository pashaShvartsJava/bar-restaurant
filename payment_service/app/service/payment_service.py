from .stripe_service import StripeService
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