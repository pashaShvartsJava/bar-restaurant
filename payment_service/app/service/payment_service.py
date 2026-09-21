from ..schemas.payment_schema import PaymentDTO
from payment_service.app.repository.payment_repository import PaymentRepository
from uuid import UUID


class PaymentService:

    def __init__(self, payment_repository : PaymentRepository):
        self.payment_repository = payment_repository

    async def create_payment(self, data : PaymentDTO, client_id : UUID):
        return await self.payment_repository.create_payment(data, client_id)