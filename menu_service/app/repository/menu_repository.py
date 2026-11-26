from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from sqlalchemy.orm import selectinload

from ..model.menu import Menu, DishStatus
from decimal import Decimal

from ..model.recipe import Recipe
from ..model.recipe_data import RecipeData
from ..schema.recipe_schema import RecipeCreate


class MenuRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_dishes(self) -> List[Menu]:
        result = await self.db.execute(select(Menu))
        return result.scalars().all()

    async def get_all_available_dishes(self, restaurant_id : UUID):
        result = await self.db.execute(select(Menu).where(Menu.dish_status==DishStatus.AVAILABLE, Menu.restaurant_id==restaurant_id))
        return result.scalars().all()

    async def get_dish_by_id(self, id : int, restaurant_id : UUID) -> Menu:
        result = await self.db.execute(select(Menu).where(Menu.id==id, Menu.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_dish_by_name(self, dish_name : str) -> Menu:
        result = await self.db.execute(select(Menu).where(Menu.dish_name==dish_name))
        return result.scalar_one_or_none()

    async def get_recipe_by_menu_id(self, menu_id : int, restaurant_id : UUID) -> Recipe | None:
        result = await self.db.execute(select(Recipe).options(
        selectinload(Recipe.menu),
        selectinload(Recipe.recipe_datas)
            .selectinload(RecipeData.product)).where(Recipe.menu_id == menu_id, Recipe.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_recipe_data(self, recipe_id : int, restaurant_id : UUID, product_id : int) -> RecipeData:
        result = await self.db.execute(select(RecipeData).options(selectinload(RecipeData.recipe)
                                                                  ,selectinload(RecipeData.product))
                                       .where(RecipeData.recipe_id == recipe_id,
                                                            RecipeData.restaurant_id == restaurant_id,
                                                            RecipeData.product_id==product_id))
        return result.scalar_one_or_none()

    async def get_recipe_datas_by_menu_id(self, menu_id : int, restaurant_id : UUID) -> list[RecipeData]:
        result = await self.db.execute(select(RecipeData).where(
                                                RecipeData.menu_id == menu_id,
                                                            Recipe.restaurant_id == restaurant_id))
        return result.scalars().all()


    async def create_dish(self, dish_name : str, price : Decimal, description : str, category_id : UUID, image_url : str, restaurant_id : UUID, is_drink : bool) -> Menu:
        new_dish = Menu(
            dish_name=dish_name,
            price=price,
            description=description,
            category_id=category_id,
            image_url=image_url,
            restaurant_id=restaurant_id,
            is_drink=is_drink
        )
        self.db.add(new_dish)
        await self.db.commit()
        await self.db.refresh(new_dish)
        return new_dish

    async def create_recipe(self, data: RecipeCreate, restaurant_id : UUID) -> Recipe:
        async with self.db.begin():
            recipe = await self.get_recipe_by_menu_id(data.menu_id, restaurant_id)
            if recipe is not None:
                for product in data.products:
                    found_recipe_data = await self.get_recipe_data(recipe.id, restaurant_id, product.product_id)
                    found_recipe_data.quantity = product.quantity
                return recipe
            new_recipe = Recipe(menu_id=data.menu_id, restaurant_id=restaurant_id)
            self.db.add(new_recipe)
            await self.db.flush()
            for product in data.products:
                new_recipe_data = RecipeData(
                    product_id=product.product_id,
                    quantity=product.quantity,
                    recipe_id=new_recipe.id,
                    restaurant_id=restaurant_id)
                self.db.add(new_recipe_data)
        await self.db.refresh(new_recipe)
        return new_recipe

    async def update_dish(self, id : int, dish_name : str, description : str, price : Decimal, image_url : str, restaurant_id : UUID) -> Menu:
        updated_dish = await self.get_dish_by_id(id, restaurant_id)
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

    async def update_dish_status(self, id : int, restaurant_id : UUID):
        updated_dish = await self.get_dish_by_id(id, restaurant_id)
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