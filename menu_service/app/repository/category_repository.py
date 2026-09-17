from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..model import Menu
from ..model.category import Category
from sqlalchemy.orm import selectinload

from ..model.menu import DishStatus


class CategoryRepository:

    def __init__ (self, db : AsyncSession):
        self.db = db

    async def get_all_categories(self) -> List[Category]:
        result = await self.db.execute(select(Category).options(selectinload(Category.dishes)))
        return result.scalars().unique().all()

    async def create_category(self, category_name : str):
        new_category = Category(category_name=category_name)
        self.db.add(new_category)
        await self.db.commit()
        await self.db.refresh(new_category)

    async def get_all_categories_for_users(self) -> List[Category]:
        result = await self.db.execute(select(Category).where(Category.dishes.any()).options(selectinload(Category.dishes)))
        return result.scalars().unique().all()