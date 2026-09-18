import re
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import date
from uuid import UUID

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