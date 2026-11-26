from ..model.product import Product
from ..repository.product_repository import ProductRepository
from typing import List


class ProductService:

    def __init__(self, product_repository : ProductRepository):
        self.product_repository = product_repository

    async def get_all_products(self) -> List[Product]:
        return await self.product_repository.get_all_products()