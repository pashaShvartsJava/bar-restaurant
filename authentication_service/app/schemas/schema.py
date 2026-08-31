from pydantic import BaseModel, Field
from datetime import date
from ..model.identity_model import IdentityRole
from uuid import UUID

class LoginSchema(BaseModel):

    email : str = Field(..., min_length=6, max_length=64, description="email")
    password : str = Field(..., min_length=8, max_length=64, description="password")

class RegisterRequestDTO(BaseModel):

    identity_id: UUID = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    email: str = Field(..., min_length=6, max_length=64, description="email")
    birthday: date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    role: IdentityRole = Field(..., description="role")

class RegisterIdentitySchema(BaseModel):

    email: str = Field(..., min_length=6, max_length=64, description="email")
    password: str = Field(..., min_length=8, max_length=64, description="password")

class RegistrationSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday: date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    role: IdentityRole = Field(..., description="role")
    email: str = Field(..., min_length=6, max_length=64, description="email")
    password: str = Field(..., min_length=8, max_length=64, description="password")

class AddressResponseDTO(BaseModel):
    city : str = Field(..., description="city")
    postal_code : int = Field(..., description="postal code")
    street : str = Field(..., description="street")
    house : int = Field(..., description="house number")
    apartment : int | None = Field(None, description="apartment number; not necessary")


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
    old_email: str | None = Field(..., min_length=6, max_length=64, description="email")
    new_email: str | None = Field(..., min_length=6, max_length=64, description="email")