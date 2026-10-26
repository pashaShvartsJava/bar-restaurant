from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.restaurant_membership_model import RestaurantMembership, MembershipStatus, MembershipRole
from ..models.restaurant_model import Restaurant, RestaurantStatus
from ..schema.restaurant_schema import RestaurantCreationDTO, KeyDTO
import logging

from ..security.role.role import IdentityRole

logger = logging.getLogger(__name__)


class RestaurantRepository:

    def __init__ (self, db : AsyncSession):
        self.db = db

    async def get_restaurant_by_id(self, restaurant_id : UUID) -> Restaurant:
        result = await self.db.execute(select(Restaurant).options(selectinload(Restaurant.memberships)).where(Restaurant.id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_membership_by_identity_id(self, identity_id : UUID) -> RestaurantMembership:
        result = await self.db.execute(select(RestaurantMembership).where(RestaurantMembership.identity_id == identity_id))
        return result.scalar_one_or_none()

    async def create_restaurant(self, data : RestaurantCreationDTO) -> Restaurant:
        async with self.db.begin():
            new_restaurant = Restaurant(
                restaurant_name=data.restaurant_name,
                slug=data.slug,
                country=data.country,
                city=data.city,
                address=data.address,
                timezone=data.timezone,
                currency=data.restaurant_currency
            )
            self.db.add(new_restaurant)
            await self.db.flush()
            new_membership = RestaurantMembership(
                restaurant_id=new_restaurant.id,
                identity_id=data.identity_id,
            )
            self.db.add(new_membership)
        await self.db.refresh(new_restaurant)
        return new_restaurant

    async def delete_saga_restaurant(self, restaurant_id : UUID):
        restaurant = await self.get_restaurant_by_id(restaurant_id)
        await self.db.delete(restaurant)
        await self.db.commit()

    async def change_restaurant_status(self, restaurant_id : UUID, new_status : str):
        found_restaurant = await self.get_restaurant_by_id(restaurant_id)
        if found_restaurant is None:
            logger.warning("Restaurant %s not found", restaurant_id)
            return

        if found_restaurant.status == RestaurantStatus.CLOSED and new_status != RestaurantStatus.CLOSED:
            logger.warning("Ignoring %s -> %s for closed restaurant %s", ...)
            return
        if new_status == "trialing" or new_status == "active":
            found_restaurant.status = RestaurantStatus.ACTIVE
        if new_status == "past_due" or new_status == "unpaid" or new_status == "paused":
            found_restaurant.status = RestaurantStatus.SUSPENDED
        if new_status == "canceled" or new_status == "incomplete_expired":
            found_restaurant.status = RestaurantStatus.CLOSED
        await self.db.flush()

    async def get_status_by_owner_and_id(self, data : KeyDTO) -> RestaurantStatus:
        result = await self.db.execute(select(RestaurantMembership)
                                       .options(selectinload(RestaurantMembership.restaurant))
                                       .where(RestaurantMembership.restaurant_id==data.restaurant_id,
                                              RestaurantMembership.identity_id==data.identity_id))
        membership : RestaurantMembership = result.scalar_one_or_none()
        return membership.restaurant.status

    async def delete_saga_membership(self, identity_id : UUID):
        found_identity = await self.get_membership_by_identity_id(identity_id)
        await self.db.delete(found_identity)
        await self.db.commit()

    async def create_membership(self, identity_id : UUID, restaurant_id : UUID, role : str):
        new_role  = None
        if role == MembershipRole.ADMIN.value:
            new_role = MembershipRole.ADMIN
        if role == MembershipRole.MODERATOR.value:
            new_role = MembershipRole.MODERATOR
        new_membership = RestaurantMembership(
            identity_id=identity_id,
            restaurant_id=restaurant_id,
            role=new_role
        )
        self.db.add(new_membership)
        await self.db.commit()
        await self.db.refresh(new_membership)




