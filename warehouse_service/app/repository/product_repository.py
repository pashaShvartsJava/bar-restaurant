from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.products_model import Product, Unit
from ..models.supplies_model import Supply


class ProductRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_product_by_id_and_restaurant_id(self, product_id : int, restaurant_id : UUID) -> Product:
        result = await self.db.execute(select(Product).where(Product.id==product_id, Product.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_supply_by_id_and_restaurant_id(self, supply_id : int, restaurant_id : UUID) -> Supply:
        result = await self.db.execute(
            select(Supply).where(Supply.id == supply_id, Supply.restaurant_id == restaurant_id))
        return result.scalar_one_or_none()

    async def get_all_products(self) -> list[Product]:
        result = await self.db.execute(select(Product).options(selectinload(Product.supplies)))
        return result.scalars().all()

    async def find_all_supplies(self)-> list[Supply]:
        result = await self.db.execute(select(Supply).options(selectinload(Supply.product)))
        return result.scalars().all()

    async def create_product(self,
                             name : str,
                             unit : Unit,
                             description : str | None,
                             restaurant_id : UUID,
                             image_url : str | None):
        new_product = Product(
            name=name,
            unit=unit,
            description=description,
            restaurant_id=restaurant_id,
            image_url=image_url
        )
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)

    async def update_product(self,
                             product_id : int,
                             name : str | None,
                             unit : Unit | None,
                             description : str | None,
                             restaurant_id : UUID,
                             image_url : str | None,
                             is_active : bool):
        found_product = await self.get_product_by_id_and_restaurant_id(product_id, restaurant_id)
        if name is not None:
            found_product.name = name
        if unit is not None:
            found_product.unit = unit
        if description is not None:
            found_product.description = description
        if image_url is not None:
            found_product.image_url = image_url
        found_product.is_active = is_active
        await self.db.commit()
        await self.db.refresh(found_product)

    async def create_supply(self, product_id : int, restaurant_id: UUID, quantity : Decimal, admin_data : dict):
        async with self.db.begin():
            found_product = await self.get_product_by_id_and_restaurant_id(product_id, restaurant_id)
            new_supply = Supply(
                quantity=quantity,
                product_id=product_id,
                restaurant_id=restaurant_id,
                payload={
                    "name" : admin_data.get("name"),
                    "surname" : admin_data.get("surname"),
                    "role" : admin_data.get("role")
                }
            )
            found_product.quantity += quantity
            if found_product.is_active is False:
                found_product.is_active = True
            self.db.add(new_supply)
        await self.db.refresh(new_supply)

    async def fix_supply(self, supply_id : int, restaurant_id : UUID, quantity : Decimal, reason : str):
        async with self.db.begin():
            found_supply = await self.get_supply_by_id_and_restaurant_id(supply_id, restaurant_id)
            old_quantity = found_supply.quantity
            quantity_diff = quantity - old_quantity
            found_product = await self.get_product_by_id_and_restaurant_id(found_supply.product_id, found_supply.restaurant_id)
            found_product.quantity += quantity_diff
            found_supply.quantity = quantity
            found_supply.reason = reason
        await self.db.refresh(found_supply)


