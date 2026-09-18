from ..models.orders import Order, OrderStatus
from ..repository.order_repository import OrderRepository
from ..schema.delivery_address_schema import DeliveryAddressDTO
from ..schema.order_item_schema import ListOrderDTO
from uuid import UUID


class OrderService:

    def __init__(self, order_repository : OrderRepository):
        self.order_repository=order_repository

    async def get_pending_by_client_id(self, client_id : UUID):
        return await self.get_pending_by_client_id(client_id)

    async def get_all_orders(self):
        return await self.order_repository.get_all_orders()

    async def create_order(self, data : ListOrderDTO, client_id : UUID) -> Order:
        pending_order = await self.get_pending_by_client_id(client_id)
        if pending_order is not None:
            return pending_order
        total_sum = 0
        for order_item in data.order_items:
            total_sum += order_item.price * order_item.quantity
        return await self.order_repository.create_order(data , client_id, total_sum)

    async def cancel_order_before_payment(self, client_id : UUID):
        return await self.order_repository.cancel_order_before_payment(client_id)

    async def update_order_status(self, client_id : UUID, status : OrderStatus):
        return await self.order_repository.update_order_status(client_id, status)

    async def create_order_address(self, order_id : int, delivery_data : DeliveryAddressDTO):
        return self.order_repository.create_order_address(order_id, delivery_data)