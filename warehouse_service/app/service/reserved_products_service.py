from uuid import UUID
from ..repository.product_repository import ProductRepository
from ..repository.reserved_products_repository import ReservedProductsRepository
from ..schema.order_item_schema import ListOrderDTO, ListOrderGuestDTO


class ReservedProductsService:

    def __init__ (self, reserved_products_repository : ReservedProductsRepository, product_repository : ProductRepository):
        self.reserved_products_repository = reserved_products_repository
        self.product_repository = product_repository

    async def create_reserved_products(self,
                                       restaurant_id:
                                       UUID, data: ListOrderDTO | ListOrderGuestDTO,
                                       order_number: str) -> dict:
        async with self.reserved_products_repository.db.begin():
            reserved_products = await self.reserved_products_repository.create_reserved_products(restaurant_id,
                                                                                                 data,
                                                                                                 order_number)
            unavailable_dishes = set()
            required_products = {}
            dishes_by_product = {}
            locked_products = {}
            for reserved_product in reserved_products:
                product_id = reserved_product.product_id
                required_products[product_id] = required_products.get(product_id, 0) + reserved_product.quantity
                dishes_by_product.setdefault(product_id, set()).add(reserved_product.menu_id)
            for product_id, required_quantity in required_products.items():
                product = await self.product_repository.get_product_by_id_and_restaurant_id_for_update(product_id,
                                                                                                       restaurant_id)
                if product is None or product.quantity < required_quantity:
                    unavailable_dishes.update(dishes_by_product[product_id])
                else:
                    locked_products[product_id] = product
            if unavailable_dishes:
                await self.product_repository.create_dish_status_changed_outbox_event(restaurant_id,
                                                                                      "DishStatusChangedEvent",
                                                                                      "unavailable",
                                                                                      [{"menu_id": menu_id} for menu_id in unavailable_dishes])
                return {"message": "InsufficientStockProductsError"}
            for product_id, required_quantity in required_products.items():
                product = locked_products[product_id]
                product.quantity -= required_quantity
                await self.product_repository.update(product)
            await self.product_repository.create_stock_changed_outbox_event(restaurant_id, "StockChangedEvent")
            return {"message": "Stock was changed"}