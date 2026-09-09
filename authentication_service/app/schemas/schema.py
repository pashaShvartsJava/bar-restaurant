import re

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import date
from ..model.identity_model import IdentityRole, Status
from uuid import UUID

class LoginSchema(BaseModel):

    email : EmailStr
    password : str

class RegisterRequestDTO(BaseModel):

    identity_id: UUID = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    email: EmailStr
    birthday: date = Field(..., description="birthday")
    phone: str
    role: IdentityRole = Field(..., description="role")

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

class RegisterIdentitySchema(BaseModel):

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64, description="password")

class RegistrationSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday: date = Field(..., description="birthday")
    phone: str
    city: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., description="postal code")
    street: str = Field(..., min_length=2, max_length=100, description="street")
    house: int = Field(..., gt=0, description="house number")
    apartment: int | None = Field(default=None, gt=0, description="apartment number; not necessary")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64, description="password")

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

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str):
        if not re.fullmatch(r"[0-9]{5}", value):
            raise ValueError("Некорректный почтовый индекс")
        return value

class AddressResponseDTO(BaseModel):
    city: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., description="postal code")
    street: str = Field(..., min_length=2, max_length=100, description="street")
    house: int = Field(..., gt=0, description="house number")
    apartment: int | None = Field(default=None, gt=0, description="apartment number; not necessary")

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str):
        if not re.fullmatch(r"[0-9]{5}", value):
            raise ValueError("Некорректный почтовый индекс")
        return value


class RegisterRequest(BaseModel):
    user_data: RegisterRequestDTO
    address_data: AddressResponseDTO

class PasswordRequest(BaseModel):
    identity_id : UUID = Field(..., description="identity_id")

class PasswordResponse(BaseModel):
    password : str = Field(..., min_length=8, description="password")

class PasswordUpdateDTO(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    new_password: str = Field(..., min_length=8, max_length=64, description="password")

class EmailRequest(BaseModel):
    old_email: EmailStr
    new_email: EmailStr

class IdentityDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID = Field(..., description="identity_id")
    email : EmailStr
    status : Status
