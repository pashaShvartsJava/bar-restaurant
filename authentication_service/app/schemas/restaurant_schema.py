from pydantic import BaseModel
import re
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import date
from ..model.identity_model import IdentityRole, Status
from uuid import UUID

class RestaurantRegistrationDTO(BaseModel):
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
    restaurant_name: str = Field(...)
    country: str = Field(...)
    city: str = Field(...)
    address: str = Field(...)