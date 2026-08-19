from ..repository import MenuRepository
from ..service.dish_service import MenuService
from ..database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session


def get_menu_service(db: Session = Depends(get_db)):
    menu_repository = MenuRepository(db)
    return MenuService(menu_repository)