from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from typing import Optional, Any

class RestaurantStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class RestaurantForUserProfileDTO(BaseModel):
    slug: str
    restaurant_name: str
    city: Optional[str] = None
    short_description: Optional[str] = None
    photo_url: Optional[str] = None
    accepts_delivery: bool
    status: RestaurantStatus

class RestaurantConstructorDTO(BaseModel):
    id: UUID
    restaurant_name: str
    slug: str
    country: str
    city: str
    address: str
    timezone: str
    currency: str
    status: str
    slogan: Optional[str] = None
    tagline: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    about_title: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    instagram_url: Optional[str] = None
    working_hours: Optional[Any] = None
    accepts_reservations: bool = True
    accepts_delivery: bool = True
    accepts_orders_on_site: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    stripe_account_id: Optional[str] = None
    stripe_charges_enabled: Optional[bool] = False
    stripe_payouts_enabled: Optional[bool] = False