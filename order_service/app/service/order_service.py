from order_service.app.repository.order_item_repository import OrderItemRepository
from order_service.app.repository.order_repository import OrderRepository
from order_service.app.schema.order_item_schema import ListOrderDTO
from uuid import UUID


class OrderService:

    def __init__(self, order_repository : OrderRepository):
        self.order_repository=order_repository

    async def create_order(self, data : ListOrderDTO, client_id : UUID):
        return await self.order_repository.create_order(data , client_id)