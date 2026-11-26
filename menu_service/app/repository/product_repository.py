import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from sqlalchemy.orm import selectinload

from ..model.product import Product, Unit


class ProductRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_products(self) -> List[Product]:
        result = await self.db.execute(select(Product).options(selectinload(Product.recipe_datas)))
        return result.scalars().all()

    async def create_product(self, name : str, unit : str, restaurant_id : str, product_id : int):
        product_unit = None
        if unit == "g":
            product_unit = Unit.GRAM
        if unit == "kg":
            product_unit = Unit.KILOGRAM
        if unit == "ml":
            product_unit = Unit.MILLILITER
        if unit == "l":
            product_unit = Unit.LITER
        if unit == "piece":
            product_unit = Unit.PIECE
        new_product = Product(
            name=name,
            unit=product_unit,
            restaurant_id=uuid.UUID(restaurant_id),
            warehouse_product_id=product_id
        )
        self.db.add(new_product)
        await self.db.flush()