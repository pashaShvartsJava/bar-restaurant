import os
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.restaurant_membership_model import RestaurantMembership, MembershipRole
from ..models.restaurant_model import Restaurant, RestaurantStatus
from ..schema.constructor_schema import UpdateRestaurantDTO
from ..schema.restaurant_schema import RestaurantCreationDTO, KeyDTO
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/app/templates/media")
RESTAURANTS_DIR = UPLOAD_DIR / "restaurants"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024


async def delete_photo_file(photo_url: str | None) -> None:
    if not photo_url:
        return
    filename = photo_url.rsplit("/", 1)[-1]
    file_path = RESTAURANTS_DIR / filename
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass


async def save_photo_file(photo: UploadFile, restaurant_id: UUID) -> str:
    if photo.content_type not in ALLOWED_TYPES:
        raise ValueError(f"Неподдерживаемый формат файла: {photo.content_type}. "
                         f"Разрешены: JPEG, PNG, WEBP.")
    contents = await photo.read()
    if len(contents) > MAX_SIZE:
        raise ValueError(f"Файл слишком большой ({len(contents) / 1024 / 1024:.1f} MB). "
                         f"Максимум {MAX_SIZE / 1024 / 1024:.0f} MB.")
    extension = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    filename = f"{restaurant_id}_{uuid.uuid4().hex}{extension}"
    RESTAURANTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RESTAURANTS_DIR / filename
    with open(file_path, "wb") as f:
        f.write(contents)
    return f"/media/restaurants/{filename}"


class RestaurantRepository:

    def __init__ (self, db : AsyncSession):
        self.db = db

    async def get_restaurant_by_name(self, name : str) -> Restaurant:
        result = await self.db.execute(
            select(Restaurant).options(selectinload(Restaurant.memberships)).where(Restaurant.restaurant_name == name))
        return result.scalar_one_or_none()

    async def get_restaurant_by_id(self, restaurant_id : UUID) -> Restaurant:
        result = await self.db.execute(select(Restaurant).options(selectinload(Restaurant.memberships)).where(Restaurant.id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_restaurant_by_slug(self, slug : str) -> Restaurant:
        result = await self.db.execute(select(Restaurant).where(Restaurant.slug==slug))
        return result.scalar_one_or_none()

    async def get_all_restaurants(self):
        result = await self.db.execute(select(Restaurant))
        return result.scalars().all()

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

    async def update_restaurant( self, restaurant_id: UUID, data: UpdateRestaurantDTO, photo: UploadFile | None = None) -> Restaurant:
        found_restaurant = await self.get_restaurant_by_id(restaurant_id)
        if not found_restaurant:
            raise ValueError("Restaurant not found")
        found_restaurant.restaurant_name = data.restaurant_name
        found_restaurant.email = data.email
        found_restaurant.slug = data.slug
        found_restaurant.currency = data.currency
        found_restaurant.timezone = data.timezone
        found_restaurant.address = data.address
        found_restaurant.country = data.country
        found_restaurant.city = data.city
        found_restaurant.phone = data.phone
        found_restaurant.description = data.description
        found_restaurant.about_title = data.about_title
        found_restaurant.accepts_delivery = data.accepts_delivery
        found_restaurant.accepts_orders_on_site = data.accepts_orders_on_site
        found_restaurant.accepts_reservations = data.accepts_reservations
        found_restaurant.instagram_url = data.instagram_url
        found_restaurant.short_description = data.short_description
        found_restaurant.slogan = data.slogan
        found_restaurant.tagline = data.tagline

        found_restaurant.working_hours = (
            {
                day: hours.model_dump() if hasattr(hours, "model_dump") else hours
                for day, hours in data.working_hours.items()
            }
            if data.working_hours
            else None
        )
        if data.remove_photo:
            await delete_photo_file(found_restaurant.photo_url)
            found_restaurant.photo_url = None
        if photo is not None and photo.filename:
            new_url = await save_photo_file(photo, restaurant_id)
            await delete_photo_file(found_restaurant.photo_url)
            found_restaurant.photo_url = new_url
        await self.db.commit()
        await self.db.refresh(found_restaurant)
        return found_restaurant

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




