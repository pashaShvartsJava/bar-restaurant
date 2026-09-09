from uuid import UUID

from ..repository.menu_repository import MenuRepository
from ..model.menu import Menu
from typing import List
from decimal import Decimal


class MenuService:

    def __init__(self, menu_repository : MenuRepository):
        self.menu_repository = menu_repository

    async def get_all_dishes(self) -> List[Menu]:
        return await self.menu_repository.get_all_dishes()

    async def get_dish_by_id(self, id : int) -> Menu:
        return await self.menu_repository.get_dish_by_id(id)

    async def get_dish_by_name(self, dish_name : str) -> Menu:
        return await self.menu_repository.get_dish_by_name(dish_name)

    async def create_dish(self, dish_name : str, price : Decimal, description : str, category_id : UUID, image_url : str) -> Menu:
        return await self.menu_repository.create_dish(dish_name, price, description, category_id, image_url)

    async def update_dish(self, id : int, updated_dish : Menu) -> Menu:
        return await self.menu_repository.update_dish(id, updated_dish)

    async def delete_dish(self, id : int) -> Menu:
        return await self.menu_repository.delete_dish(id)