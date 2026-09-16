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

    async def get_or_create_admin_conversation(self, identity_id: UUID, admin_id : UUID):
        conversation = await self.conversation_repository.get_conversation_by_identity_id(identity_id)
        if conversation is None:
            return await self.conversation_repository.create_admin_conversation(identity_id, admin_id)
        else:
            if conversation.admin_id is not None and conversation.admin_id==admin_id:
                return conversation
            if conversation.admin_id is None:
                await self.conversation_repository.take_conversation_by_admin(admin_id, conversation)
            else:
                raise ValueError("This customer is already taken by another administrator")
            return conversation

    async def get_conversation_by_id(self, conversation_id : int) -> Conversation:
        return await self.conversation_repository.get_conversation_by_id(conversation_id)

    async def free_conversation(self, conversation_id : int):
        return await self.conversation_repository.free_conversation(conversation_id)

    async def mark_as_read_by_user(self, conversation_id : int, message_id : int):
        return await self.conversation_repository.mark_as_read_by_user(conversation_id, message_id)

    async def mark_as_read_by_admin(self, conversation_id: int, message_id: int):
        return await self.conversation_repository.mark_as_read_by_admin(conversation_id, message_id)