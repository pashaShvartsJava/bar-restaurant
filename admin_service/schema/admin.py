from datetime import date

from pydantic import BaseModel, Field
from admin_service.model.admin import AdminRole


class AdminBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")
    birthday : date = Field(..., description="birthday")
    phone: str = Field(..., min_length=6, max_length=14, description="phone number")
    email: str = Field(..., min_length=6, max_length=64, description="email")
    password: str= Field(..., min_length=8, max_length=64, description="password")
    role : AdminRole = Field(..., description="role")

class AdminRegistrationDTO(AdminBase):
    pass

class AdminRegistrationUpdate(AdminBase):
    pass

class AdminRegistrationResponse(AdminBase):
    name: str = Field(..., min_length=2, max_length=50, description="name")
    surname: str = Field(..., min_length=2, max_length=50, description="surname")