from sqlalchemy import Column, Integer, DECIMAL, ForeignKey, UniqueConstraint, UUID
from sqlalchemy.orm import relationship

from ..database.database import Base


class RecipeData(Base):

    __tablename__ = "recipe_data"
    __table_args__ = (UniqueConstraint("recipe_id", "product_id", name="uq_recipe_product"),)

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(DECIMAL(10, 2), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)

    product = relationship("Product", back_populates="recipe_datas")
    recipe = relationship("Recipe", back_populates="recipe_datas")