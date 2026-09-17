from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from order_service.app.models.order_items import OrderItem
from order_service.app.models.orders import Order
from order_service.app.schema.order_item_schema import ListOrderDTO


class OrderRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def create_order(self, order_items : ListOrderDTO, client_id : UUID):
        new_order = Order(
            client_id=client_id
        )
        self.db.add(new_order)
        await self.db.flush()

        total_sum = 0
        for order_item in order_items:
            new_order_item = OrderItem(
                order_id=new_order.id,
                dish_id=order_item.dish_id,
                dish_name=order_item.dish_name,
                quantity=order_item.quantity,
                price=order_item.price
            )
            self.db.add(new_order_item)
            total_sum += new_order_item.price * new_order_item.quantity
        new_order.sum = total_sum

        await self.db.commit()
        await self.db.refresh(new_order)


