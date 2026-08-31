from pydantic import BaseModel, Field
from datetime import date
from uuid import UUID

from .address_schema import AddressResponseDTO
from ..model.user_model import IdentityRole

class RegisterResponseDTO(BaseModel):

    identity_id: UUID = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    email : str = Field(..., min_length=6, max_length=64, description="email")
    birthday: date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    role: IdentityRole = Field(..., description="role")

class RegisterRequest(BaseModel):

    user_data : RegisterResponseDTO
    address_data : AddressResponseDTO

class UserEditSchema(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50, description="name")
    surname: str | None = Field(None, min_length=2, max_length=50, description="surname")
    birthday: date | None = Field(None, description="birthday")
    phone: str | None = Field(None, min_length=6, max_length=14, description="phone number")
    email: str | None = Field(None, min_length=6, max_length=64, description="email")
    city: str | None = Field(None, description="city")
    postal_code: int | None = Field(None, description="postal code")
    street: str | None = Field(None, description="street")
    house: int | None = Field(None, description="house number")
    apartment: int | None = Field(None, description="apartment number; not necessary")

class IdentityRequest(BaseModel):
    identity_id : UUID = Field(..., description="identity_id")

class PasswordResponse(BaseModel):
    password : str = Field(..., min_length=8, description="password")

class PasswordDTO(BaseModel):
    identity_id: UUID = Field(..., description="identity_id")
    new_password: str = Field(..., min_length=8, max_length=64, description="password")

class EmailRequest(BaseModel):
    old_email: str | None = Field(..., min_length=6, max_length=64, description="email")
    new_email: str | None = Field(..., min_length=6, max_length=64, description="email")