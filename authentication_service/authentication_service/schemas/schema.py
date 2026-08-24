from pydantic import BaseModel, Field
from datetime import date
from ..model.identity_model import IdentityRole

class LoginSchema(BaseModel):

    email : str = Field(..., min_length=6, max_length=64, description="email")
    password : str = Field(..., min_length=8, max_length=64, description="password")

class RegisterRequestDTO(BaseModel):

    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
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