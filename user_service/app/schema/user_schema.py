import re

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import date
from uuid import UUID

from .address_schema import AddressResponseDTO
from ..model.user_model import IdentityRole

class RegisterResponseDTO(BaseModel):

    identity_id: UUID = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    email : EmailStr = Field(..., min_length=6, max_length=64, description="email")
    birthday: date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    role: IdentityRole = Field(..., description="role")

    @field_validator("birthday")
    @classmethod
    def validate_age(cls, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Регистрация доступна только с 18 лет")
        return value

class RegisterRequest(BaseModel):

    user_data : RegisterResponseDTO
    address_data : AddressResponseDTO


class UserEditSchema(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50, description="name")
    surname: str | None = Field(None, min_length=2, max_length=50, description="surname")
    email: EmailStr | None
    phone: str | None
    birthday: date | None = Field(None, description="birthday")
    city: str | None = Field(None, min_length=2, max_length=100)
    postal_code: str | None = Field(None, description="postal code")
    street: str | None = Field(None, min_length=2, max_length=100, description="street")
    house: int | None = Field(None, gt=0, description="house number")
    apartment: int | None = Field(default=None, gt=0, description="apartment number; not necessary")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str):
        if not re.fullmatch(r"\+?[0-9]{10,15}", value):
            raise ValueError("Некорректный номер телефона")
        return value

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str):
        if not re.fullmatch(r"[0-9]{5}", value):
            raise ValueError("Некорректный почтовый индекс")
        return value

    @field_validator("birthday")
    @classmethod
    def validate_age(cls, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Регистрация доступна только с 18 лет")
        return value


class IdentityRequest(BaseModel):
    identity_id : UUID = Field(..., description="identity_id")

class PasswordResponse(BaseModel):
    password : str = Field(..., min_length=8, description="password")

class PasswordDTO(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    new_password: str = Field(..., min_length=8, max_length=64, description="password")

class EmailRequest(BaseModel):
    old_email: EmailStr | None = Field(..., min_length=6, max_length=64, description="email")
    new_email: EmailStr | None = Field(..., min_length=6, max_length=64, description="email")