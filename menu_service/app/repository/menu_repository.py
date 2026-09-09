from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..model.menu import Menu, DishStatus
from decimal import Decimal

class MenuRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_dishes(self) -> List[Menu]:
        result = await self.db.execute(select(Menu))
        return result.scalars().all()

    async def get_dish_by_id(self, id : int) -> Menu:
        result = await self.db.execute(select(Menu).where(Menu.id==id))
        return result.scalar_one_or_none()

    async def get_dish_by_name(self, dish_name : str) -> Menu:
        result = await self.db.execute(select(Menu).where(Menu.dish_name==dish_name))
        return result.scalar_one_or_none()

    async def create_dish(self, dish_name : str, price : Decimal, description : str, category_id : UUID, image_url : str) -> Menu:
        new_dish = Menu(
            dish_name=dish_name,
            price=price,
            description=description,
            category_id=category_id,
            image_url=image_url
        )
        self.db.add(new_dish)
        await self.db.commit()
        await self.db.refresh(new_dish)
        return new_dish

    async def update_dish(self, id : int, dish_name : str, description : str, price : Decimal, image_url : str) -> Menu:
        updated_dish = await self.get_dish_by_id(id)
        if dish_name is not None:
            updated_dish.dish_name = dish_name
        if description is not None:
            updated_dish.description = description
        if price is not None:
            updated_dish.price = price
        if image_url is not None:
            updated_dish.image_url = image_url

        await self.db.commit()
        await self.db.refresh(updated_dish)
        return updated_dish

    async def update_dish_status(self, id : int):
        updated_dish = await self.get_dish_by_id(id)
        if updated_dish.dish_status == DishStatus.AVAILABLE:
            updated_dish.dish_status = DishStatus.UNAVAILABLE
        else:
            updated_dish.dish_status = DishStatus.AVAILABLE
        await self.db.commit()
        await self.db.refresh(updated_dish)
        return updated_dish

    async def delete_dish(self, id : int) -> Menu:
        old_dish = await self.get_dish_by_id(id)

        await self.db.delete(old_dish)
        await self.db.commit()

        return old_dish