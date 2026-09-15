import uuid

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship


from ..database.database import Base


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    admin_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), nullable=False)

    messages = relationship("Message", back_populates="conversation")