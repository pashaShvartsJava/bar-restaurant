from typing import Optional
from pydantic import BaseModel


class WorkingHoursDay(BaseModel):
    from_: Optional[str] = None
    to: Optional[str] = None


class UpdateRestaurantDTO(BaseModel):
    restaurant_name: str
    slug: str
    slogan: Optional[str] = None
    tagline: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    about_title: Optional[str] = None
    country: str
    city: str
    address: str
    timezone: str
    currency: str = "EUR"
    phone: Optional[str] = None
    email: Optional[str] = None
    instagram_url: Optional[str] = None
    working_hours: Optional[dict] = None
    accepts_reservations: bool = True
    accepts_delivery: bool = True
    accepts_orders_on_site: bool = True
    remove_photo: bool = False