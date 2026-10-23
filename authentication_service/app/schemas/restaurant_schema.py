from enum import Enum
from zoneinfo import ZoneInfoNotFoundError, ZoneInfo

import pycountry
from pydantic import BaseModel
import re
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import date

from .subscription_schema import SubscriptionDTO
from uuid import UUID

class RestaurantStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class RestaurantRegistrationDTO(SubscriptionDTO):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday: date = Field(..., description="birthday")
    phone: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64, description="password")
    restaurant_name: str = Field(...)
    country: str = Field(...)
    city: str = Field(...)
    address: str = Field(...)
    slug: str = Field(...)
    restaurant_currency: str = Field(...)
    timezone: str = Field(...)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str):
        if not re.fullmatch(r"\+?[0-9]{10,15}", value):
            raise ValueError("Некорректный номер телефона")
        return value

    @field_validator("birthday")
    @classmethod
    def validate_age(cls, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Регистрация доступна только с 18 лет")
        return value

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