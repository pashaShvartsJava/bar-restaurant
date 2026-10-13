from decimal import Decimal

from pydantic import BaseModel, Field
from uuid import UUID

from ..models.orders import OrderStatus


class StatusDTO(BaseModel):
    status : OrderStatus

class MergeOrdersDTO(BaseModel):
    order_ids: list[UUID]
    table_number: int = Field(..., ge=1)