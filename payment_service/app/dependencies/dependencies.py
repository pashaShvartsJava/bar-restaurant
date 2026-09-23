from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..repository.payment_repository import PaymentRepository
from ..service.payment_service import PaymentService

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.stripe_service import StripeService
from ..broker.instance import rabbitmq

def get_payment_service_dependency(db: AsyncSession = Depends(get_db)):
    return PaymentService(db, PaymentRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db))