
from ..repository import MenuRepository
from ..model import Menu
from typing import List, Optional

class MenuService:

    def __init__(self, menu_repository : MenuRepository):
        self.menu_repository = menu_repository

    def get_all_dishes(self) -> List[Menu]:
        return self.menu_repository.get_all_dishes()

    def get_dish_by_id(self, id : int) -> Menu:
        return self.menu_repository.get_dish_by_id(id)

    def get_dish_by_name(self, dish_name : str) -> Menu:
        return self.menu_repository.get_dish_by_name(dish_name)

    def create_dish(self, dish_name : str, price : float, description : str) -> Menu:
        return self.menu_repository.create_dish(dish_name, price, description)

    def update_dish(self, id : int, updated_dish : Menu) -> Menu:
        return self.menu_repository.update_dish(id, updated_dish)

    def delete_dish(self, id : int) -> Menu:
        return self.menu_repository.delete_dish(id)