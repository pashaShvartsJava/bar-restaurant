from pydantic import BaseModel
from typing import List


class RecipeProduct(BaseModel):
    product_id: int
    quantity: float


class RecipeCreate(BaseModel):
    menu_id: int
    products: List[RecipeProduct]