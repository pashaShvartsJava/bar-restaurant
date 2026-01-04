from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

class Admin(Base):

    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    surname  = Column(String, index=True, nullable=False)
    birthday = Column(DateTime, index=True, nullable=False)
    phone = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    password = Column(String, nullable=False, unique=True)
