from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, String, DECIMAL, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..database.database import Base
from enum import Enum

class Recipe(Base):

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menu.id"), nullable=False, unique=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)

    menu = relationship("Menu", back_populates="recipe")
    recipe_datas = relationship("RecipeData", back_populates="recipe")