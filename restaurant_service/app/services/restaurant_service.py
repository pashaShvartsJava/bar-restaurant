from uuid import UUID


from ..models.restaurant_model import Restaurant, RestaurantStatus
from ..repositories.restaurant_repository import RestaurantRepository
from ..schema.restaurant_schema import RestaurantCreationDTO, KeyDTO


class RestaurantService:

    def __init__(self, restaurant_repository : RestaurantRepository):
        self.restaurant_repository = restaurant_repository

    async def create_restaurant(self, data: RestaurantCreationDTO) -> Restaurant:
        return await self.restaurant_repository.create_restaurant(data)

    async def delete_saga_restaurant(self, restaurant_id: UUID):
        return await self.restaurant_repository.delete_saga_restaurant(restaurant_id)

    async def get_status_by_owner_and_id(self, data: KeyDTO) -> RestaurantStatus:
        return await self.restaurant_repository.get_status_by_owner_and_id(data)