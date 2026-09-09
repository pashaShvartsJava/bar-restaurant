from pydantic import BaseModel, Field
from decimal import Decimal


class MenuDTO(BaseModel):

    dish_name: str = Field(..., min_length=2, max_length=50, description="name of the dish")
    price: Decimal = Field(..., ge=1, le=20000)
    description: str = Field(..., min_length=0, max_length=100, description="components of the dish")