from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from ..database import Base

class Address(Base):

    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    postal_code = Column(Integer, nullable=False)
    street = Column(String, nullable=False)
    house = Column(Integer, nullable=False)
    apartment = Column(Integer)

    users = relationship("User", back_populates="address")