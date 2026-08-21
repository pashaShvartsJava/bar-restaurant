from sqlalchemy.orm import Session
from typing import List, Optional
from menu_service.schema import menu
from ..model import Menu

class MenuRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all_dishes(self) -> List[Menu]:
        return self.db.query(Menu).all()

    def get_dish_by_id(self, id : int) -> Menu:
        return self.db.query(Menu).get(id)

    def get_dish_by_name(self, name : str) -> Menu:
        return self.db.query(Menu).filter(Menu.dish_name==name)

    def create_dish(self, dish_name : str, price : float, description : str) -> Menu:
        new_dish = Menu(
            dish_name = dish_name,
            price = price,
            description = description
        )
        self.db.add(new_dish)
        self.db.commit()
        self.db.refresh(new_dish)
        return new_dish

    def update_dish(self, id : int, new_dish : Menu) -> Menu:
        updated_dish = self.get_dish_by_id(id)

        updated_dish.dish_name = new_dish.dish_name
        updated_dish.price = new_dish.price
        updated_dish.description = new_dish.description

        self.db.commit()
        self.db.refresh(updated_dish)
        return updated_dish

    def delete_dish(self, id : int) -> Menu:
        old_dish = self.get_dish_by_id(id)

        self.db.delete(old_dish)
        self.db.commit()

        return old_dish