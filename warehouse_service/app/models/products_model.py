from sqlalchemy import Column, DateTime, String, Enum as SQLEnum, func, Integer, ForeignKey, Boolean, DECIMAL
from sqlalchemy.dialects.postgresql  import UUID
from enum import Enum

from sqlalchemy.orm import relationship

from ..database.database import Base

class Unit(str, Enum):
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    LITER = "l"
    PIECE = "piece"


class Product(Base):

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    unit = Column(SQLEnum(Unit), nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by_order_online = Column(DateTime(timezone=True), nullable=True)

    supplies = relationship("Supply", back_populates="product")
