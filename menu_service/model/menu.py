from sqlalchemy import Column, Integer, String, DECIMAL
from decimal import Decimal
from sqlalchemy.orm import relationship
from menu_service.database import Base

class Menu(Base):

    __tablename__ = 'menu'

    id = Column(Integer, primary_key=True, index=True)
    dish_name = Column(String, index=True, nullable=False)
    price = Column(DECIMAL, nullable=False, index=True)
    description = Column(String, index=True)