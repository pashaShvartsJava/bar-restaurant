from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, String, DECIMAL, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..database.database import Base
from enum import Enum

class Unit(str, Enum):
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    LITER = "l"
    PIECE = "piece"

class Product(Base):

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_product_id = Column(Integer, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False, unique=True)
    unit = Column(SQLEnum(Unit), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)

    recipe_datas = relationship("RecipeData", back_populates="product")