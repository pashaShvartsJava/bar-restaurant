import uuid

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum


from ..database.database import Base

class SenderRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    sender_role = Column(SQLEnum(SenderRole), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")