from decimal import Decimal

from pydantic import BaseModel, Field
from uuid import UUID


class PaymentDTO(BaseModel):
    order_id: int = Field(...)
    order_number: UUID = Field(...)
    sum: Decimal = Field(...)