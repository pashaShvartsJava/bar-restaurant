from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base
from sqlalchemy import Column, String

class Key(Base):

    __tablename__ = "keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    registration_key = Column(String, unique=True)
    authentication_key = Column(String, unique=True)