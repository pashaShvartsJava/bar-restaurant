from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel

CURRENCY_SYMBOLS = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "RUB": "₽",
    "KZT": "₸",
    "UAH": "₴",
    "TRY": "₺",
    "CHF": "₣",
    "PLN": "zł",
    "GEL": "₾",
}


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