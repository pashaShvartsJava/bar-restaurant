import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, EmailStr
from ..model.admin import AdminRole, Status
from ..security.role.role import IdentityRole


class AdminBase(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday : date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    role : AdminRole = Field(..., description="role")

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

class AdminRegistration(AdminBase):
    pass

class AdminUpdateDTO(BaseModel):
    name: str  | None= Field(None, min_length=2, max_length=50, description="name")
    surname: str | None = Field(None, min_length=2, max_length=50, description="surname")
    phone: str | None
    birthday: date | None = Field(None, description="birthday")
    role: IdentityRole | None = Field(None, description="role")
    email: EmailStr | None

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

class AdminRegistrationDTO(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday: date = Field(..., description="birthday")
    phone: str
    email: EmailStr

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

class IdentityEdit(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    email: EmailStr | None
    role: IdentityRole | None= Field(None, description="role")

class AdminRegistrationForm(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday: date = Field(..., description="birthday")
    phone: str
    email: EmailStr
    password: str = Field(..., min_length=8, description="password")
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

class AddAdminRequest(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    email : EmailStr
    role: IdentityRole = Field(..., description="role")
    password: str = Field(..., min_length=8, description="password")
    status : Status
