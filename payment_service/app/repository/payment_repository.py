from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payments import Payment
from ..schemas.payment_schema import PaymentDTO
from uuid import UUID


class PaymentRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def get_by_id(self, payment_id: int) -> Payment:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one()

    async def get_all_payments(self, restaurant_id : UUID):
        result = await self.db.execute(select(Payment).where(Payment.restaurant_id==restaurant_id))
        return result.scalars().all()

    async def create_payment(self, data : PaymentDTO, client_id : UUID) -> Payment:
        new_payment = Payment(
            order_id=data.order_id,
            order_number=data.order_number,
            sum=data.sum,
            client_id=client_id,
            restaurant_id=data.restaurant_id
        )
        self.db.add(new_payment)
        await self.db.flush()
        return new_payment

    async def save(self, payment : Payment) -> Payment:
        await self.db.commit()
        await self.db.refresh(payment)
        return payment