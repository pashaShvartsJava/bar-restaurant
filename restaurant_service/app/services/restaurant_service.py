from uuid import UUID

from ..models.restaurant_model import Restaurant
from ..repositories.restaurant_repository import RestaurantRepository
from ..schema.restaurant_schema import RestaurantCreationDTO


class RestaurantService:

    def __init__(self, restaurant_repository : RestaurantRepository):
        self.restaurant_repository = restaurant_repository

    async def create_restaurant(self, data: RestaurantCreationDTO) -> Restaurant:
        return await self.restaurant_repository.create_restaurant(data)

    async def delete_saga_restaurant(self, restaurant_id: UUID):
        return await self.restaurant_repository.delete_saga_restaurant(restaurant_id)