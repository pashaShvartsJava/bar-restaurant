from uuid import UUID

from ..models.products_model import Product, Unit
from ..repository.product_repository import ProductRepository


class ProductService:

    def __init__ (self, product_repository : ProductRepository):
        self.product_repository = product_repository

    async def get_all_products(self) -> list[Product]:
        return await self.product_repository.get_all_products()

    async def create_product(self,
                             name: str,
                             unit: Unit,
                             description: str | None,
                             restaurant_id: UUID,
                             image_url: str | None):
        return await self.product_repository.create_product(name, unit, description, restaurant_id, image_url)

    async def update_product(self,
                             product_id: int,
                             name: str | None,
                             unit: Unit | None,
                             description: str | None,
                             restaurant_id: UUID,
                             image_url: str | None,
                             is_active: bool):
        return await self.product_repository.update_product(product_id, name, unit, description, restaurant_id, image_url, is_active)