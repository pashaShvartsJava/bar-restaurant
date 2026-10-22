from ..repository.outbox_repository import OutboxPaymentEventsRepository
from ..repository.payment_repository import PaymentRepository
from ..repository.subscription_repository import SubscriptionRepository
from ..service.payment_service import PaymentService

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.stripe_service import StripeService
from ..broker.instance import rabbitmq
from ..service.subscription_service import SubscriptionService


def get_payment_service_dependency(db: AsyncSession = Depends(get_db)):
    return PaymentService(db, PaymentRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db))

def get_subscription_service_dependency(db: AsyncSession = Depends(get_db)):
    return SubscriptionService(db, SubscriptionRepository(db), StripeService(), rabbitmq, OutboxPaymentEventsRepository(db))