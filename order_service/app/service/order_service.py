from datetime import date
from decimal import Decimal

from ..models.orders import Order, OrderStatus
from ..repository.order_repository import OrderRepository
from ..schema.delivery_address_schema import DeliveryAddressDTO
from ..schema.order_item_schema import ListOrderDTO
from uuid import UUID


class OrderService:

    def __init__(self, order_repository : OrderRepository):
        self.order_repository=order_repository

    async def get_order_by_id(self, order_id: int) -> Order:
        return await self.order_repository.get_order_by_id(order_id)

    async def get_all_orders_history(self):
        return await self.order_repository.get_all_orders_history()

    async def get_pending_by_client_id(self, client_id : UUID):
        return await self.order_repository.get_pending_by_client_id(client_id)

    async def get_all_orders(self):
        return await self.order_repository.get_all_orders()

    async def create_order(self, data : ListOrderDTO, client_id : UUID) -> Order:
        pending_order = await self.get_pending_by_client_id(client_id)
        if pending_order is not None:
            pending_order.status = OrderStatus.CANCELLED_BEFORE
        total_sum = 0
        for order_item in data.order_items:
            total_sum += order_item.price * order_item.quantity
        return await self.order_repository.create_order(data , client_id, total_sum)

    async def cancel_order_before_payment(self, client_id : UUID):
        return await self.order_repository.cancel_order_before_payment(client_id)

    async def update_order_status(self, client_id : UUID, status : OrderStatus) -> Order:
        return await self.order_repository.update_order_status(client_id, status)

    async def create_order_address(self, order_id : int, delivery_data : DeliveryAddressDTO):
        return await self.order_repository.create_order_address(order_id, delivery_data)

    async def mark_order_as_expired(self):
        return await self.order_repository.mark_order_as_expired()

    async def search_or_sort_orders(self, search: str,
                                    status: OrderStatus,
                                    date_from: date,
                                    date_to: date,
                                    sum_from: Decimal,
                                    sum_to: Decimal,
                                    sort: str):
        return await self.order_repository.search_or_sort_orders(search, status, date_from, date_to, sum_from, sum_to, sort)

    async def find_order_by_client_id(self, client_id: UUID):
        return await self.order_repository.find_order_by_client_id(client_id)

    async def get_user_history_orders(self, client_id : UUID):
        return await self.order_repository.get_user_history_orders(client_id)

    async def get_user_active_orders(self, client_id: UUID):
        return await self.order_repository.get_user_active_orders(client_id)

    async def get_user_last_completed_order(self, client_id: UUID):
        return await self.order_repository.get_user_last_completed_order(client_id)