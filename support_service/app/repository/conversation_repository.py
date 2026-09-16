from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Message
from ..models.conversation import Conversation
from sqlalchemy import or_, select, func
from ..security.role.role import IdentityRole
from uuid import UUID

class ConversationRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_conversation_by_id(self, conversation_id : int) -> Conversation:
        result = await self.db.execute(select(Conversation).where(Conversation.id==conversation_id))
        return result.scalar_one_or_none()

    async def get_conversation_by_identity_id(self, identity_id) -> Conversation | None:
        result = await self.db.execute(select(Conversation).options(selectinload(Conversation.messages)).
                                       where(or_(Conversation.user_id==identity_id, Conversation.admin_id==identity_id)))
        return result.scalar_one_or_none()

    async def create_conversation(self, identity_id):
        now = datetime.now(timezone.utc)
        new_conversation = Conversation(
            user_id=identity_id,
            created_at=now
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)

    async def create_admin_conversation(self, identity_id, admin_id):
        now = datetime.now(timezone.utc)
        new_conversation = Conversation(
            user_id=identity_id,
            admin_id=admin_id,
            created_at=now
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)

    async def get_unread_conversations(self):
        result = await self.db.execute(select(Conversation)
                                        .join(Conversation.messages)
                                        .group_by(Conversation.id)
                                        .having(Conversation.last_read_message_by_admin_id < func.max(Message.id)))
        return result.scalars().all()

    async def take_conversation_by_admin(self, admin_id : UUID, conversation : Conversation):
        conversation.admin_id = admin_id
        await self.db.commit()
        await self.db.refresh(conversation)

    async def free_conversation(self, conversation_id : int):
        conversation = await self.get_conversation_by_id(conversation_id)
        conversation.admin_id = None
        await self.db.commit()
        await self.db.refresh(conversation)

    async def mark_as_read_by_user(self, conversation_id: int, message_id: int):
        result  = await self.db.execute(select(Conversation).join(Message).where(Conversation.id==conversation_id).where(Message.id==message_id))
        conversation : Conversation = result.scalar_one_or_none()
        if conversation.last_read_message_by_user_id is None or message_id > conversation.last_read_message_by_user_id:
            conversation.last_read_message_by_user_id = message_id
        await self.db.commit()
        await self.db.refresh(conversation)


    async def mark_as_read_by_admin(self, conversation_id: int, message_id: int):
        result = await self.db.execute(
            select(Conversation).join(Message).where(Conversation.id == conversation_id).where(
                Message.id == message_id))
        conversation: Conversation = result.scalar_one_or_none()
        if conversation.last_read_message_by_admin_id is None or message_id > conversation.last_read_message_by_admin_id:
            conversation.last_read_message_by_admin_id = message_id
        await self.db.commit()
        await self.db.refresh(conversation)
