from decimal import Decimal

from pydantic import BaseModel, Field
from uuid import UUID

from ..models.orders import OrderStatus


class StatusDTO(BaseModel):
    status : OrderStatus