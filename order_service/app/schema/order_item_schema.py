from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import date
from uuid import UUID

class OrderItemDTO(BaseModel):

    dish_id : int = Field(...,)
    dish_name: str = Field(...,)
    price: Decimal = Field(..., ge=1, le=20000)
    quantity: int = Field(...,)

class ListOrderDTO(BaseModel):
    order_items : list[OrderItemDTO]

class ListOrderGuestDTO(BaseModel):
    client_id : UUID= Field(...)
    order_items: list[OrderItemDTO]