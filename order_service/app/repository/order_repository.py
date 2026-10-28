import uuid
from datetime import datetime, timezone, timedelta, date, time
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.delivery_address import DeliveryAddress
from ..models.order_items import OrderItem
from ..models.orders import Order, OrderStatus
from ..models.outbox_change_status_events_model import OutboxChangeStatusEvents
from ..schema.delivery_address_schema import DeliveryAddressDTO
from ..schema.order_item_schema import ListOrderDTO, ListOrderGuestDTO, SplitOrderDTO
from ..schema.orders_schema import MergeOrdersDTO


class OrderRepository:

    def __init__(self, db : AsyncSession):
        self.db=db

    async def get_order_by_id(self, order_id : int, restaurant_id : UUID) -> Order:
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items),
                                                             selectinload(Order.address)).where(Order.id==order_id, Order.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_order_by_order_number(self, order_number : UUID, restaurant_id : UUID) -> Order:
        result = await self.db.execute(
            select(Order).options(selectinload(Order.order_items), selectinload(Order.address)).where(
                Order.order_number == order_number, Order.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_order_by_client_id(self, client_id : UUID) -> Order:
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items), selectinload(Order.address))
                                       .where(Order.client_id==client_id, Order.status==OrderStatus.CONFIRMED_ADDRESS)
                                       .order_by(Order.created_at.desc()).limit(1))
        return result.scalar_one_or_none()

    async def get_pending_by_client_id(self, client_id : UUID, restaurant_id : UUID) -> Order:
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items))
                                       .where(Order.client_id==client_id,
                                              Order.status==OrderStatus.PENDING,
                                              Order.restaurant_id==restaurant_id)
                                       .order_by(Order.created_at.desc()).limit(1))
        return result.scalar_one_or_none()

    async def get_all_orders_history(self, restaurant_id : UUID):
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items)).where(Order.created_at<today,
                                                                                                    Order.restaurant_id==restaurant_id))
        return result.scalars().all()

    async def get_all_orders(self, restaurant_id : UUID):
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items))
                                       .order_by(Order.created_at.desc())
                                       .where(Order.restaurant_id==restaurant_id))
        return result.scalars().all()

    async def get_unpaid_order_by_client(self, client_id : UUID, restaurant_id : UUID) -> Order:
        result = await self.db.execute(select(Order).where(Order.client_id==client_id,
                                                           Order.status==OrderStatus.PENDING,
                                                           Order.restaurant_id==restaurant_id))
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

    async def create_order(self, order_items : ListOrderDTO, client_id : UUID, total_sum : Decimal, restaurant_id : UUID) -> Order:
        async with self.db.begin():
            new_order = Order(
                client_id=client_id,
                sum=total_sum,
                restaurant_id=restaurant_id
            )
            self.db.add(new_order)
            await self.db.flush()

            for order_item in order_items.order_items:
                new_order_item = OrderItem(
                    order_id=new_order.id,
                    dish_id=order_item.dish_id,
                    dish_name=order_item.dish_name,
                    quantity=order_item.quantity,
                    price=order_item.price,
                    restaurant_id=restaurant_id
                )
                self.db.add(new_order_item)
        await self.db.refresh(new_order)
        return new_order

    async def create_order_for_guest(self, data : ListOrderGuestDTO, total_sum : Decimal, status : str, table_number : int | None, restaurant_id : UUID):
        if status == "":
            order_status = OrderStatus.PENDING
        else:
            order_status = OrderStatus.INTERNAL_ORDER
        if table_number is None:
            number = None
        else:
            number = table_number
        async with self.db.begin():
            new_order = Order(
                client_id=data.client_id,
                sum=total_sum,
                status=order_status,
                table_number=number,
                restaurant_id=restaurant_id
            )
            self.db.add(new_order)
            await self.db.flush()

            for order_item in data.order_items:
                new_order_item = OrderItem(
                    order_id=new_order.id,
                    dish_id=order_item.dish_id,
                    dish_name=order_item.dish_name,
                    quantity=order_item.quantity,
                    price=order_item.price,
                    restaurant_id=restaurant_id
                )
                self.db.add(new_order_item)
        await self.db.refresh(new_order)
        return new_order

    async def cancel_order_before_payment(self, client_id: UUID, restaurant_id : UUID):
        old_order = await self.get_unpaid_order_by_client(client_id, restaurant_id)
        old_order.status = OrderStatus.CANCELLED_BEFORE
        await self.db.commit()
        await self.db.refresh(old_order)

    async def update_order_status(self, client_id : UUID, status : OrderStatus, restaurant_id : UUID) -> Order:
        old_order = await self.get_pending_by_client_id(client_id, restaurant_id)
        old_order.status = status
        await self.db.commit()
        await self.db.refresh(old_order)
        return old_order

    async def mark_order_as_paid(self, order_id : int, status : OrderStatus) -> Order:
        old_order = await self.get_order_by_id(order_id)
        old_order.status = status
        await self.db.flush()
        return old_order

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
                                    sort : str,
                                    restaurant_id : UUID):
        query = select(Order).options(selectinload(Order.order_items)).where(Order.restaurant_id==restaurant_id)
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

    async def find_orders_by_client_id(self, client_id : UUID, restaurant_id : UUID):
        result = await self.db.execute(select(Order).options(selectinload(Order.order_items))
                                       .where(Order.client_id==client_id, Order.restaurant_id==restaurant_id)
                                       .order_by(Order.created_at.desc()))
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

    async def change_order_status(self, status : OrderStatus, email : str | None, order_number : UUID, restaurant_id : UUID):
        async with self.db.begin():
            order = await self.get_order_by_order_number(order_number, restaurant_id)
            order.status = status
            if email is not None:
                await self.create_outbox_change_status_event(email, order)
        await self.db.refresh(order)

    async def create_outbox_change_status_event(self, email : str, order : Order) -> OutboxChangeStatusEvents:
        order_items = [
            {
                "dish_id": item.dish_id,
                "dish_name": item.dish_name,
                "quantity": item.quantity,
                "price": str(item.price),
            }
            for item in order.order_items
        ]
        new_outbox = OutboxChangeStatusEvents(
            event_type="ChangeOrderStatus",
            payload={
                "client_id" : str(order.client_id),
                "order_number" : str(order.order_number),
                "order_status" : order.status.value,
                "email" : email,
                "order_items" : order_items,
                "sum" : str(order.sum)
            },
            event_id=str(uuid.uuid4())
        )
        self.db.add(new_outbox)
        await self.db.flush()
        return new_outbox

    async def get_all_unpublished_events(self):
        result = await self.db.execute(select(OutboxChangeStatusEvents).where(OutboxChangeStatusEvents.published_at.is_(None)))
        return result.scalars().all()

    async def mark_event_as_published(self, event: OutboxChangeStatusEvents):
        event.published_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def merge_orders(self, data: MergeOrdersDTO, restaurant_id : UUID):
        async with self.db.begin():
            orders = []
            for order_id in data.order_ids:
                order = await self.get_order_by_id(order_id, restaurant_id)
                if order is None:
                    raise ValueError(f"Заказ {order_id} не найден")
                orders.append(order)
            merged_order = Order(
                client_id=uuid.uuid4(),
                status=OrderStatus.INTERNAL_ORDER,
                table_number=data.table_number,
                sum=0,
                restaurant_id=restaurant_id
            )
            self.db.add(merged_order)
            await self.db.flush()
            for order in orders:
                merged_order.sum += order.sum
                for item in order.order_items:
                    new_item = OrderItem(
                        order_id=merged_order.id,
                        dish_id=item.dish_id,
                        dish_name=item.dish_name,
                        quantity=item.quantity,
                        price=item.price,
                        restaurant_id=restaurant_id
                    )
                    self.db.add(new_item)
            await self.db.flush()
            for order in orders:
                await self.db.delete(order)
            await self.db.flush()
        await self.db.refresh(merged_order)
        return merged_order

    async def split_order(self, data : SplitOrderDTO, restaurant_id : UUID):
        async with self.db.begin():
            for order_guest_dto in data.list_order_guest_dto:
                total_sum = 0
                for order_item in order_guest_dto.order_items:
                    total_sum += order_item.price * order_item.quantity
                new_order = Order(
                    client_id=order_guest_dto.client_id,
                    sum=total_sum,
                    status=OrderStatus.INTERNAL_ORDER,
                    table_number=data.table_number,
                    restaurant_id=restaurant_id
                )
                self.db.add(new_order)
                await self.db.flush()

                for order_item in order_guest_dto.order_items:
                    new_order_item = OrderItem(
                        order_id=new_order.id,
                        dish_id=order_item.dish_id,
                        dish_name=order_item.dish_name,
                        quantity=order_item.quantity,
                        price=order_item.price,
                        restaurant_id=restaurant_id
                    )
                    self.db.add(new_order_item)
            old_order = await self.get_order_by_id(data.old_order_id, restaurant_id)
            if old_order is None:
                raise ValueError("Исходный заказ не найден")
            await self.db.delete(old_order)

    async def get_revenue(self, date_from: date | None, date_to: date | None):
        revenue = 0
        if date_from is None and date_to is None:
            today = date.today()
            start_date = today.replace(day=1)
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
            stmt = (select(Order).where(Order.created_at >= start_date, Order.created_at < next_month,
                                        or_(
                                            and_(Order.status == OrderStatus.COMPLETED, Order.table_number.is_(None)),
                                            and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            for order in orders:
                revenue += order.sum
            return revenue
        if date_from is not None and date_to is None:
            stmt = (select(Order).where(Order.created_at >= date_from,
                                        or_(
                                            and_(Order.status == OrderStatus.COMPLETED, Order.table_number.is_(None)),
                                            and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            for order in orders:
                revenue += order.sum
            return revenue
        if date_from is None and date_to is not None:
            raise ValueError("Enter starting date")
        if date_from is not None and date_to is not None:
            stmt = (select(Order).where(Order.created_at >= date_from, Order.created_at <= date_to,
                                        or_(
                                            and_(Order.status == OrderStatus.COMPLETED, Order.table_number.is_(None)),
                                            and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            for order in orders:
                revenue += order.sum
            return revenue
        return None

    async def get_order_count(self, date_from: date | None, date_to: date | None):
        if date_from is None and date_to is None:
            today = date.today()
            start_date = today.replace(day=1)
            if date_from is None and date_to is None:
                today = date.today()
                start_date = today.replace(day=1)
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
            stmt = (select(Order).where(Order.created_at>=start_date, Order.created_at < next_month,
                           or_(
                               and_(Order.status==OrderStatus.COMPLETED, Order.table_number.is_(None)),
                               and_(Order.table_number.is_not(None), Order.status==OrderStatus.PAID))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            return len(orders)
        if date_from is not None and date_to is None:
            stmt = (select(Order).where(Order.created_at >= date_from,
                                        or_(
                                            and_(Order.status == OrderStatus.COMPLETED, Order.table_number.is_(None)),
                                            and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID))))
            result = await self.db.execute(stmt)
            orders: list[Order] = result.scalars().all()
            return len(orders)
        if date_from is None and date_to is not None:
            raise ValueError("Enter starting date")
        if date_from is not None and date_to is not None:
            stmt = (select(Order).where(Order.created_at >= date_from, Order.created_at <= date_to,
                                        or_(
                                            and_(Order.status == OrderStatus.COMPLETED, Order.table_number.is_(None)),
                                            and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID))))
            result = await self.db.execute(stmt)
            orders: list[Order] = result.scalars().all()
            return len(orders)
        return None

    async def get_revenue_for_previous_period(self, date_from: date | None, date_to: date | None):
        revenue = 0
        today = date.today()
        end_date = today.replace(day=1)
        start_date = (end_date - timedelta(days=1)).replace(day=1)
        if date_from is None and date_to is None:
            stmt = (select(Order).where(Order.created_at >= start_date, Order.created_at < end_date,
                or_(
                    and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID),
                    and_(Order.table_number.is_(None), Order.status == OrderStatus.COMPLETED))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            for order in orders:
                revenue += order.sum
            return revenue
        if date_from is not None and date_to is None:
            day_dif = (today - date_from).days
            start_date = date_from - timedelta(days=day_dif)
            stmt = (select(Order).where(Order.created_at >= start_date,
                           or_(
                               and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID),
                               and_(Order.table_number.is_(None), Order.status == OrderStatus.COMPLETED))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            for order in orders:
                revenue += order.sum
            return revenue
        if date_from is None and date_to is not None:
            raise ValueError("Enter starting date")
        if date_from is not None and date_to is not None:
            day_dif = (date_to - date_from).days
            start_date = date_from - timedelta(days=day_dif)
            stmt = (select(Order).where(Order.created_at >= start_date, Order.created_at < date_to,
                           or_(
                               and_(Order.table_number.is_not(None), Order.status == OrderStatus.PAID),
                               and_(Order.table_number.is_(None), Order.status == OrderStatus.COMPLETED))))
            result = await self.db.execute(stmt)
            orders : list[Order] = result.scalars().all()
            for order in orders:
                revenue += order.sum
            return revenue
        return None

    async def get_top_dishes(self, date_from: date | None, date_to: date | None) -> list[dict]:
        today = date.today()
        if date_from is None:
            date_from = today.replace(day=1)
        if date_to is None:
            if today.month == 12:
                date_to = date(today.year + 1, 1, 1)
            else:
                date_to = date(today.year, today.month + 1, 1)
        else:
            date_to += timedelta(days=1)
        start_datetime = datetime.combine(date_from, time.min)
        end_datetime = datetime.combine(date_to, time.min)
        stmt = (select(Order).options(selectinload(Order.order_items)).where(
                Order.created_at >= start_datetime,
                Order.created_at < end_datetime,
                or_(
                    and_(
                        Order.status == OrderStatus.COMPLETED,
                        Order.table_number.is_(None),
                    ),
                    and_(
                        Order.table_number.is_not(None),
                        Order.status == OrderStatus.PAID))))
        result = await self.db.execute(stmt)
        orders = result.scalars().all()
        dishes = {}
        for order in orders:
            for item in order.order_items:
                name = item.dish_name
                if name not in dishes:
                    dishes[name] = {
                        "name": name,
                        "quantity": 0,
                        "revenue": 0
                    }
                dishes[name]["quantity"] += item.quantity
                dishes[name]["revenue"] += item.price * item.quantity
        return [{**dish,
                "quantity": int(dish["quantity"]),
                "revenue": float(dish["revenue"] or 0)}
            for dish in sorted(dishes.values(), key=lambda dish: dish["quantity"], reverse=True)]

    async def get_monthly_sales(self, date_from: date | None = None, date_to: date | None = None,) -> list[dict]:
        today = date.today()
        if date_from is None:
            date_from = today.replace(day=1)
        if date_to is None:
            next_month = (date_to.replace(day=1) + timedelta(days=32) if date_to is not None else None)
            if today.month == 12:
                date_to = date(today.year + 1, 1, 1)
            else:
                date_to = date(today.year, today.month + 1, 1)
        start_datetime = datetime.combine(date_from, time.min)
        end_datetime = datetime.combine(date_to, time.min)
        stmt = (select(
                func.date(Order.created_at).label("label"),
                func.coalesce(func.sum(Order.sum), 0).label("revenue"),
                func.count(Order.id).label("order_count"),
            )
            .where(
                Order.created_at >= start_datetime,
                Order.created_at < end_datetime,
                or_(
                    and_(
                        Order.table_number.is_not(None),
                        Order.status == OrderStatus.PAID,
                    ),
                    and_(
                        Order.table_number.is_(None),
                        Order.status == OrderStatus.COMPLETED)))
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at)))
        result = await self.db.execute(stmt)
        rows = result.all()
        return [{
                    "label": row.label.strftime("%d.%m"),
                    "revenue": float(row.revenue),
                    "order_count": row.order_count
                }for row in rows]












