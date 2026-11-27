import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.outbox_events_model import OutboxEvent
from ..models.products_model import Product, Unit
from ..models.reserved_products_model import ReservedProduct
from ..models.supplies_model import Supply
from ..schema.order_item_schema import ListOrderDTO, ListOrderGuestDTO


class ReservedProductsRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def create_reserved_products(self, restaurant_id: UUID, data: ListOrderDTO | ListOrderGuestDTO, order_number : str) -> list[ReservedProduct]:
        list = []
        for dish in data.order_items:
            for recipe_data in dish.recipe_data:
                new_reserved_product = ReservedProduct(
                    order_number=order_number,
                    menu_id=dish.dish_id,
                    product_id=recipe_data.product_id,
                    quantity=recipe_data.quantity,
                    restaurant_id=restaurant_id)
                self.db.add(new_reserved_product)
                list.append(new_reserved_product)
        await self.db.flush()
        return list

    async def update(self, reserved_product : ReservedProduct):
        await self.db.flush()
        await self.db.refresh(reserved_product)