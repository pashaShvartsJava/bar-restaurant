from uuid import UUID

from select import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.restaurant_membership_model import RestaurantMembership
from ..models.restaurant_model import Restaurant
from ..schema.restaurant_schema import RestaurantCreationDTO


class RestaurantRepository:

    def __init__ (self, db : AsyncSession):
        self.db = db

    async def get_restaurant_by_id(self, restaurant_id : UUID) -> Restaurant:
        result = await self.db.execute(select(Restaurant).options(selectinload(Restaurant.memberships)).where(Restaurant.id==restaurant_id))
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

