import secrets

from sqlalchemy.dialects.postgresql import UUID
import uuid

from sqlalchemy.orm import relationship

from ..database import Base
from sqlalchemy import Column, String, ForeignKey


class Key(Base):

    __tablename__ = "keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    authentication_key = Column(String, unique=True, default=secrets.token_urlsafe(32))
    restaurant_id = Column(String, unique=True, nullable=False)

    identities = relationship("Identity", back_populates="key",uselist=True, cascade="all, delete-orphan")