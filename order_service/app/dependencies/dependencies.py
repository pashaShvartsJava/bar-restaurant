from ..repository.order_repository import OrderRepository
from ..service.order_service import OrderService

from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_order_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = OrderRepository(db)
    return OrderService(menu_repository)