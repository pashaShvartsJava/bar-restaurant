from datetime import datetime

from pydantic import BaseModel, Field
from pydantic_extra_types.epoch import Integer


class AdminBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday : datetime = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=12, description="phone number")
    email: str = Field(..., min_length=6, max_length=64, description="email")
    password: str= Field(..., min_length=8, max_length=64, description="password")

class AdminRegistrationCreate(AdminBase):
    pass

class AdminRegistrationUpdate(AdminBase):
    pass

class AdminRegistrationResponse(AdminBase):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")