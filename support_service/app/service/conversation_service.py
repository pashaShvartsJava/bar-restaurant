from ..models import Conversation
from ..repository.conversation_repository import ConversationRepository
from uuid import UUID
from ..security.role.role import IdentityRole


class ConversationService:

    def __init__(self, conversation_repository : ConversationRepository):
        self.conversation_repository=conversation_repository

    async def get_or_create_conversation(self, identity_id : UUID):
        conversation = await self.conversation_repository.get_conversation_by_identity_id(identity_id)
        if conversation is None:
            return await self.conversation_repository.create_conversation(identity_id)
        else:
            return conversation

    async def get_conversation_by_id(self, conversation_id : int) -> Conversation:
        return await self.conversation_repository.get_conversation_by_id(conversation_id)