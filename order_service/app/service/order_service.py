from datetime import date
from decimal import Decimal

from ..models.guest_customers import GuestCustomer
from ..models.orders import Order, OrderStatus
from ..repository.guest_repository import GuestRepository
from ..repository.order_repository import OrderRepository
from ..schema.delivery_address_schema import DeliveryAddressDTO, GuestCustomerDTO
from ..schema.order_item_schema import ListOrderDTO, ListOrderGuestDTO
from uuid import UUID
import httpx
from ..config.config import settings

INTERNAL_TOKEN = settings.internal_token


class OrderService:

    def __init__(self, order_repository : OrderRepository, guest_repository : GuestRepository):
        self.order_repository=order_repository
        self.guest_repository = guest_repository

    async def get_order_by_id(self, order_id: int) -> Order:
        return await self.order_repository.get_order_by_id(order_id)

    async def get_customer_by_client_id(self, client_id: UUID) -> GuestCustomer:
        return await self.guest_repository.get_customer_by_client_id(client_id)

    async def get_order_by_order_number(self, order_number: UUID) -> Order:
        return await self.order_repository.get_order_by_order_number(order_number)

    async def get_all_orders_history(self):
        return await self.order_repository.get_all_orders_history()

    async def get_pending_by_client_id(self, client_id : UUID):
        return await self.order_repository.get_pending_by_client_id(client_id)

    async def get_all_orders(self):
        return await self.order_repository.get_all_orders()

    async def create_guest_order(self, data : GuestCustomerDTO, client_id : UUID):
        return await self.guest_repository.create_guest_order(data, client_id)

    async def create_order(self, data : ListOrderDTO, client_id : UUID | None) -> Order:
        pending_order = await self.get_pending_by_client_id(client_id)
        if pending_order is not None:
            pending_order.status = OrderStatus.CANCELLED_BEFORE
        total_sum = 0
        for order_item in data.order_items:
            total_sum += order_item.price * order_item.quantity
        await self.order_repository.db.rollback()
        return await self.order_repository.create_order(data , client_id, total_sum)

    async def create_order_for_guest(self, data : ListOrderGuestDTO, status : str, table_number : int | None):
        total_sum = 0
        for order_item in data.order_items:
            total_sum += order_item.price * order_item.quantity
        await self.order_repository.db.rollback()
        return await self.order_repository.create_order_for_guest(data , total_sum, status, table_number)

    async def mark_order_as_paid(self, order_id: int, status: OrderStatus) -> Order:
        return await self.order_repository.mark_order_as_paid(order_id, status)

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

    async def find_orders_by_client_id(self, client_id: UUID):
        return await self.order_repository.find_orders_by_client_id(client_id)

    async def get_user_history_orders(self, client_id : UUID):
        return await self.order_repository.get_user_history_orders(client_id)

    async def get_user_active_orders(self, client_id: UUID):
        return await self.order_repository.get_user_active_orders(client_id)

    async def get_user_last_completed_order(self, client_id: UUID):
        return await self.order_repository.get_user_last_completed_order(client_id)

    async def change_order_status(self, status: OrderStatus, email : str, order_number : UUID):
        await self.order_repository.db.rollback()
        return await self.order_repository.change_order_status(status, email, order_number)

    async def get_customer_email(self, client_id: UUID) -> str:
        customer = await self.get_customer_by_client_id(client_id)

        if customer is not None:
            return customer.email

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url="http://authentication-service:8000/get_client",
                cookies={
                    "guest_client_id": str(client_id)
                },
                headers={
                    "internal_token": INTERNAL_TOKEN
                },
            )
            response.raise_for_status()
        return response.json()