from pydantic import BaseModel, Field
from datetime import date
from ..model.identity_model import IdentityRole

class LoginSchema(BaseModel):

    email : str = Field(..., min_length=6, max_length=64, description="email")
    password : str = Field(..., min_length=8, max_length=64, description="password")

class RegisterRequestDTO(BaseModel):

    identity_id: str = Field(..., description="identity_id")
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
    apartment : int = Field(..., description="apartment number; not necessary")


class RegisterRequest(BaseModel):
    user_data: RegisterRequestDTO
    address_data: AddressResponseDTO