from uuid import UUID

from ..models.restaurant_membership_model import RestaurantMembership
from ..models.restaurant_model import Restaurant, RestaurantStatus
from ..repositories.restaurant_repository import RestaurantRepository
from ..schema.restaurant_schema import RestaurantCreationDTO, KeyDTO
from ..security.role.role import IdentityRole


class RestaurantService:

    def __init__(self, restaurant_repository : RestaurantRepository):
        self.restaurant_repository = restaurant_repository

    async def get_all_restaurants(self):
        return await self.restaurant_repository.get_all_restaurants()

    async def get_restaurant_by_slug(self, slug: str) -> Restaurant:
        return await self.restaurant_repository.get_restaurant_by_slug(slug)

    async def create_restaurant(self, data: RestaurantCreationDTO) -> Restaurant:
        return await self.restaurant_repository.create_restaurant(data)

    async def delete_saga_restaurant(self, restaurant_id: UUID):
        return await self.restaurant_repository.delete_saga_restaurant(restaurant_id)

    async def get_status_by_owner_and_id(self, data: KeyDTO) -> RestaurantStatus:
        return await self.restaurant_repository.get_status_by_owner_and_id(data)

    async def delete_saga_membership(self, identity_id: UUID):
        return await self.restaurant_repository.delete_saga_membership(identity_id)

    async def get_membership_by_identity_id(self, identity_id: UUID) -> RestaurantMembership:
        return await self.restaurant_repository.get_membership_by_identity_id(identity_id)

    async def create_membership(self, identity_id: UUID, restaurant_id: UUID, role: str):
        return await self.restaurant_repository.create_membership(identity_id, restaurant_id, role)