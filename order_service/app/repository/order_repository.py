from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ..models.order_items import OrderItem
from ..models.orders import Order, OrderStatus
from ..schema.order_item_schema import ListOrderDTO


class OrderRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def get_pending_by_client_id(self, client_id : UUID) -> Order:
        result = await self.db.execute(select(Order).where(Order.client_id==client_id, Order.status==OrderStatus.PENDING))
        return result.scalar_one_or_none()

    async def get_all_orders(self):
        result = await self.db.execute(select(Order))
        return result.scalars().all()

    async def get_unpaid_order_by_client(self, client_id : UUID) -> Order:
        result = await self.db.execute(select(Order).where(Order.client_id==client_id, Order.status==OrderStatus.PENDING))
        return result.scalar_one_or_none()

    async def create_order(self, order_items : ListOrderDTO, client_id : UUID, total_sum : Decimal):
        new_order = Order(
            client_id=client_id,
            sum=total_sum
        )
        self.db.add(new_order)
        await self.db.flush()

        for order_item in order_items.order_items:
            new_order_item = OrderItem(
                order_id=new_order.id,
                dish_id=order_item.dish_id,
                dish_name=order_item.dish_name,
                quantity=order_item.quantity,
                price=order_item.price
            )
            self.db.add(new_order_item)

        await self.db.commit()
        await self.db.refresh(new_order)

    async def cancel_order_before_payment(self, client_id: UUID):
        old_order = await self.get_unpaid_order_by_client(client_id)
        old_order.status = OrderStatus.CANCELLED_BEFORE
        await self.db.commit()
        await self.db.refresh(old_order)

    async def update_order_status(self, client_id : UUID, status : OrderStatus):
        old_order = await self.get_pending_by_client_id(client_id)
        old_order.status = status
        await self.db.commit()
        await self.db.refresh(old_order)


