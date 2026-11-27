from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class Unit(str, Enum):
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    LITER = "l"
    PIECE = "piece"

class RecipeProductDto(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0)
    unit: Unit

class OrderItemDTO(BaseModel):
    dish_id : int = Field(...,)
    dish_name: str = Field(...,)
    price: Decimal = Field(..., ge=1, le=20000)
    quantity: int = Field(...,)
    is_drink: bool = Field(...)
    recipe_data: list[RecipeProductDto] = Field(default_factory=list)

class ListOrderDTO(BaseModel):
    order_items : list[OrderItemDTO]

class ListOrderGuestDTO(BaseModel):
    client_id : UUID= Field(...)
    order_items: list[OrderItemDTO]

class SplitOrderDTO(BaseModel):
    table_number: int
    old_order_id: int
    list_order_guest_dto: list[ListOrderGuestDTO]

