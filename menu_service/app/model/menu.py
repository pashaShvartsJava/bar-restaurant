from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, String, DECIMAL, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from ..database.database import Base
from enum import Enum


class DishStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

class Menu(Base):

    __tablename__ = 'menu'

    id = Column(Integer, primary_key=True, index=True)
    dish_name = Column(String, index=True, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False, index=True)
    description = Column(String, index=True)
    dish_status = Column(SQLEnum(DishStatus), default=DishStatus.AVAILABLE)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    image_url = Column(String)

    category = relationship("Category", back_populates="dishes")
