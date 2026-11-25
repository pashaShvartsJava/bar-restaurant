from sqlalchemy import Column, DateTime, func, Integer, ForeignKey, DECIMAL, String
from sqlalchemy.dialects.postgresql import UUID, JSONB

from sqlalchemy.orm import relationship

from ..database.database import Base

class Supply(Base):

    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(DECIMAL(10, 2), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    reason = Column(String, nullable=False, server_default="")

    product = relationship("Product", back_populates="supplies")
