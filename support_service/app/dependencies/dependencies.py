from ..repository.conversation_repository import ConversationRepository
from ..service.conversation_service import ConversationService
from ..repository.message_repository import MessageRepository
from ..service.message_service import MessageService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_conversation_service_dependency(db : AsyncSession = Depends(get_db)):
    return ConversationService(ConversationRepository(db))

def get_message_service_dependency(db : AsyncSession = Depends(get_db)):
    return MessageService(MessageRepository(db))