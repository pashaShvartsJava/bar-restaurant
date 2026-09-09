import uuid
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ..database.database import Base

class Category(Base):

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = Column(String, nullable=False)

    dishes = relationship("Menu", back_populates="category")