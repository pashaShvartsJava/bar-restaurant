from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payments import Payment
from ..schemas.payment_schema import PaymentDTO
from uuid import UUID


class PaymentRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def create_payment(self, data : PaymentDTO, client_id : UUID):
        new_payment = Payment(
            order_id=data.order_id,
            order_number=data.order_number,
            sum=data.sum,
            client_id=client_id
        )
        self.db.add(new_payment)
        await self.db.commit()
        await self.db.refresh(new_payment)