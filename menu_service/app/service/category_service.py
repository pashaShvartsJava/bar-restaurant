from ..repository.category_repository import CategoryRepository
from ..model.menu import Menu
from typing import List


class CategoryService:

    def __init__(self, category_service : CategoryRepository):
        self.category_service = category_service

    async def get_all_categories(self) -> List[Menu]:
        return await self.category_service.get_all_categories()

    async def create_category(self, category_name : str):
        return await self.category_service.create_category(category_name)