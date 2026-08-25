from pydantic import BaseModel, Field
from datetime import date

from .AdressSchema import AddressResponseDTO
from ..model.user_model import IdentityRole

class RegisterResponseDTO(BaseModel):

    identity_id: str = Field(..., description="identity_id")
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    email : str = Field(..., min_length=6, max_length=64, description="email")
    birthday: date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    role: IdentityRole = Field(..., description="role")

class RegisterRequest(BaseModel):

    user_data : RegisterResponseDTO
    address_data : AddressResponseDTO