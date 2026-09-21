from ..repository.payment_repository import PaymentRepository
from ..service.payment_service import PaymentService

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.stripe_service import StripeService


def get_payment_service_dependency(db: AsyncSession = Depends(get_db)):
    return PaymentService(PaymentRepository(db), StripeService())