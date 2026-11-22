from uuid import UUID

from ..models import Message
from ..repository.message_repository import MessageRepository


class MessageService:

    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def create_message(self, conversation_id: int, sender_id: UUID, sender_role, text: str) -> Message:
        return await self.message_repository.create_message(conversation_id, sender_id, sender_role, text)