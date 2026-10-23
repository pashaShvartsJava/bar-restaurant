from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator
import pycountry


class RestaurantCreationDTO(BaseModel):
    restaurant_name: str = Field(..., min_length=2, max_length=100)
    country: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=3, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    restaurant_currency: str = Field(..., min_length=3, max_length=3)
    timezone: str = Field(..., min_length=1, max_length=64)
    identity_id: UUID = Field(...)

    @field_validator("restaurant_name", "city", "address")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        value = value.strip().upper()
        if not pycountry.countries.get(alpha_2=value):
            raise ValueError("Недопустимый код страны ISO 3166-1 alpha-2")
        return value

    @field_validator("restaurant_currency")
    @classmethod
    def validate_restaurant_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if not pycountry.currencies.get(alpha_3=value):
            raise ValueError("Недопустимый код валюты ISO 4217")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        value = value.strip()
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Недопустимый часовой пояс IANA")
        return value

class KeyDTO(BaseModel):
    restaurant_id: UUID
    identity_id : UUID