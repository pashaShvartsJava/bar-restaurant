import decimal
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from sqlalchemy.orm import selectinload

from ..models.delivery_address import DeliveryAddress
from ..models.order_items import OrderItem
from ..models.orders import Order, OrderStatus
from ..schema.delivery_address_schema import DeliveryAddressDTO
from ..schema.order_item_schema import ListOrderDTO


class OrderRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def get_order_by_id(self, order_id : int) -> Order:
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items), selectinload(Order.address)).where(Order.id==order_id))
        return result.scalar_one_or_none()

    async def get_pending_by_client_id(self, client_id : UUID) -> Order:
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items))
                                       .where(Order.client_id==client_id, Order.status==OrderStatus.PENDING))
        return result.scalar_one_or_none()

    async def get_all_orders_history(self):
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items)).where(Order.created_at<today))
        return result.scalars().all()

    async def get_all_orders(self):
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items)))
        return result.scalars().all()

    async def get_unpaid_order_by_client(self, client_id : UUID) -> Order:
        result = await self.db.execute(select(Order).where(Order.client_id==client_id, Order.status==OrderStatus.PENDING))
        return result.scalar_one_or_none()

    async def create_order_address(self, order_id : int, delivery_data : DeliveryAddressDTO) -> DeliveryAddress:
        new_delivery_address = DeliveryAddress(
            order_id=order_id,
            city=delivery_data.city,
            street=delivery_data.street,
            postal_code=delivery_data.postal_code,
            house=delivery_data.house,
            apartment=delivery_data.apartment
        )
        self.db.add(new_delivery_address)
        await self.db.commit()
        await self.db.refresh(new_delivery_address)
        return new_delivery_address

    async def create_order(self, order_items : ListOrderDTO, client_id : UUID, total_sum : Decimal) -> Order:
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
        return new_order

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

    async def mark_order_as_expired(self):
        now = datetime.now(timezone.utc)
        expiration_time = now - timedelta(minutes=10)
        result = await self.db.execute(
            select(Order).where(Order.created_at <= expiration_time))
        orders = result.scalars().all()
        for order in orders:
            if order.status == OrderStatus.PENDING or order.status == OrderStatus.CONFIRMED_ADDRESS:
                order.status = OrderStatus.EXPIRED
                order.updated_status = now
        await self.db.commit()

    async def search_or_sort_orders(self, search : str,
                                    status : OrderStatus,
                                    date_from : date,
                                    date_to : date,
                                    sum_from : Decimal,
                                    sum_to : Decimal,
                                    sort : str):
        query = select(Order).options(selectinload(Order.order_items))
        if search is not None:
            query = query.where(Order.order_number == search)
        if status is not None:
            query = query.where(Order.status == status)
        if date_from is not None:
            query = query.where(Order.created_at >= date_from)
        if date_to is not None:
            query = query.where(Order.created_at <= date_to)
        if sum_from is not None:
            query = query.where(Order.sum >= sum_from)
        if sum_to is not None:
            query = query.where(Order.sum <= sum_to)

        if sort == "created_desc":
            query = query.order_by(Order.created_at.desc())
        elif sort == "created_asc":
            query = query.order_by(Order.created_at.asc())
        elif sort == "sum_desc":
            query = query.order_by(Order.sum.desc())
        elif sort == "sum_asc":
            query = query.order_by(Order.sum.asc())
        else:
            query = query.order_by(Order.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def find_order_by_client_id(self, client_id : UUID):
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items)).where(Order.client_id==client_id).order_by(Order.created_at.desc()))
        return result.scalars().all()

    async def get_user_history_orders(self, client_id : UUID):
        result = await self.db.execute(
            select(Order).options(selectinload(Order.order_items) ,selectinload(Order.address)).where(Order.client_id == client_id,
                                                                         Order.status==OrderStatus.COMPLETED)
                                                                         .order_by(Order.created_at.desc()))
        return result.scalars().all()

    async def get_user_active_orders(self, client_id : UUID):
        result = await self.db.execute(
            select(Order).options(selectinload(Order.order_items)).where(Order.client_id == client_id,
                                                                         Order.status.in_([OrderStatus.PAID,
                                                                                          OrderStatus.PREPARING,
                                                                                          OrderStatus.DELIVERING])))
        return result.scalars().all()

    async def get_user_last_completed_order(self, client_id : UUID):
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items), selectinload(Order.address))
                                 .where(Order.client_id == client_id, Order.status==OrderStatus.COMPLETED)
                                 .order_by(Order.created_at.desc()).limit(1))
        return result.scalar_one_or_none()








