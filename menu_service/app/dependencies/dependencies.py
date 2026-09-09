from ..repository.menu_repository import MenuRepository
from ..repository.category_repository import CategoryRepository
from ..service.dish_service import MenuService
from ..service.category_service import CategoryService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_menu_service_dependency(db: AsyncSession = Depends(get_db)):
    menu_repository = MenuRepository(db)
    return MenuService(menu_repository)

def get_category_service_dependency(db: AsyncSession = Depends(get_db)):
    category_repository = CategoryRepository(db)
    return CategoryService(category_repository)