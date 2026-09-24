import re

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import date

class DeliveryAddressDTO(BaseModel):

    city: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., description="postal code")
    street: str = Field(..., min_length=2, max_length=100, description="street")
    house: int = Field(..., gt=0, description="house number")
    apartment: int | None= Field(default=None, gt=0, description="apartment number; not necessary")

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str):
        if not re.fullmatch(r"[0-9]{5}", value):
            raise ValueError("Некорректный почтовый индекс")
        return value


class GuestDTO(DeliveryAddressDTO):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    email: EmailStr = Field(..., min_length=6, max_length=64, description="email")
    birthday: date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")

    @field_validator("birthday")
    @classmethod
    def validate_age(cls, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Регистрация доступна только с 18 лет")
        return value