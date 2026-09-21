from ..repository.payment_repository import PaymentRepository
from ..service.payment_service import PaymentService

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_payment_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = PaymentRepository(db)
    return PaymentService(menu_repository)