from datetime import timezone, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .stripe_service import StripeService
from ..broker.rabbitmq import RabbitMQ
from ..models.payments import PaymentStatus, Payment
from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..schemas.payment_schema import PaymentDTO
from ..repository.payment_repository import PaymentRepository
from uuid import UUID


class PaymentService:

    def __init__(self,
                 db : AsyncSession,
                 payment_repository : PaymentRepository,
                 stripe_service : StripeService,
                 rabbitmq : RabbitMQ,
                 outbox_repository : OutboxPaymentEventsRepository):

        self.db = db
        self.stripe_service = stripe_service
        self.payment_repository = payment_repository
        self.rabbitmq = rabbitmq
        self.outbox_repository = outbox_repository

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
        async with self.db.begin():
            payment = await self.payment_repository.get_by_id(int(payment_id))
            payment.stripe_session_id = session["id"]
            payment.stripe_payment_intent_id = session["payment_intent"]
            payment.status = PaymentStatus.PAID
            payment.updated_status = datetime.now(timezone.utc)
            await self.outbox_repository.create_outbox_event(payment.id, payment.order_id, payment.client_id)
        return payment