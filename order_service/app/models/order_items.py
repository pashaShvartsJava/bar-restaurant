from sqlalchemy import Column, Integer, ForeignKey, String, DECIMAL
from sqlalchemy.orm import relationship


from ..database.database import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    dish_id = Column(Integer, nullable=False)
    dish_name = Column(String, index=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False, index=True)

    order = relationship("Order", back_populates="order_items")