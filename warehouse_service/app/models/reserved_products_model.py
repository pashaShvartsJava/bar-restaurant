from enum import Enum

from sqlalchemy import Column, DateTime, func, Integer, ForeignKey, DECIMAL, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB

from sqlalchemy.orm import relationship

from ..database.database import Base

class ReservedProductStatus(str, Enum):
    RESERVED = "reserved"
    CONSUMED = "consumed"
    RETURNED_TO_WAREHOUSE = "returned_to_warehouse"


class ReservedProduct(Base):

    __tablename__ = "reserved_products"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(9), nullable=False, unique=True)
    product_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)
    quantity = Column(DECIMAL(10, 3), nullable=False)
    status = Column(SQLEnum(ReservedProductStatus), nullable=False, default=ReservedProductStatus.RESERVED)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
