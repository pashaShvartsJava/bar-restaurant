import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Message
from ..models.conversation import Conversation
from sqlalchemy import or_, select, func, exists

from ..models.message import SenderRole
from uuid import UUID

PLATFORM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

class ConversationRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_conversation_by_id(self, conversation_id : int, restaurant_id : UUID) -> Conversation:
        result = await self.db.execute(select(Conversation).options(selectinload(Conversation.messages))
                                       .where(Conversation.id==conversation_id, Conversation.restaurant_id==restaurant_id))
        return result.scalar_one_or_none()

    async def get_conversation_by_identity_id(self, identity_id, restaurant_id : UUID) -> Conversation | None:
        result = await self.db.execute(select(Conversation).options(selectinload(Conversation.messages))
                                       .where(Conversation.restaurant_id==restaurant_id)
                                       .where(or_(Conversation.user_id==identity_id, Conversation.admin_id==identity_id)))
        return result.scalar_one_or_none()

    async def create_conversation(self, identity_id : UUID, restaurant_id : UUID):
        now = datetime.now(timezone.utc)
        new_conversation = Conversation(
            user_id=identity_id,
            created_at=now,
            restaurant_id=restaurant_id
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)

    async def create_admin_conversation(self, identity_id, admin_id, restaurant_id):
        now = datetime.now(timezone.utc)
        new_conversation = Conversation(
            user_id=identity_id,
            admin_id=admin_id,
            created_at=now,
            restaurant_id=restaurant_id
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)

    async def get_unread_conversations(self, restaurant_id : UUID):
        result = await self.db.execute(select(Conversation)
                                        .where(Conversation.restaurant_id==restaurant_id)
                                        .join(Conversation.messages)
                                        .group_by(Conversation.id)
                                        .having(Conversation.last_read_message_by_admin_id < func.max(Message.id)))
        return result.scalars().all()

    async def take_conversation_by_admin(self, admin_id : UUID, conversation : Conversation, restaurant_id : UUID):
        conversation.admin_id = admin_id
        conversation.restaurant_id = restaurant_id
        await self.db.commit()
        await self.db.refresh(conversation)

    async def free_conversation(self, conversation_id : int, restaurant_id : UUID):
        conversation = await self.get_conversation_by_id(conversation_id, restaurant_id)
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

    async def count_unread_conversations(self, restaurant_id : UUID):
        result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(exists(select(Message.id).where(
            Message.conversation_id == Conversation.id,
                        Message.sender_role == SenderRole.USER,
                        Message.id > Conversation.last_read_message_by_admin_id,
                        Conversation.restaurant_id==restaurant_id))))
        return result.scalar_one()

    async def find_b2b_chats(self):
        result = await self.db.execute(select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.is_platform_chat==True))
        return result.scalars().all()

    async def find_b2c_chats(self):
        result = await self.db.execute(select(Conversation).where(Conversation.is_platform_chat==True))
        return result.scalars().all()

    async def create_fdc_conversation(self, restaurant_id : UUID) -> Conversation:
        now = datetime.now(timezone.utc)
        new_fdc_conversation = Conversation(
            user_id=PLATFORM_USER_ID,
            admin_id=restaurant_id,
            created_at=now,
            restaurant_id=restaurant_id,
            is_platform_chat=True
        )
        self.db.add(new_fdc_conversation)
        await self.db.flush()
        conversation_id = new_fdc_conversation.id
        await self.db.commit()
        result = await self.db.execute(select(Conversation)
                                       .options(selectinload(Conversation.messages))
                                       .where(Conversation.id == conversation_id))
        return result.scalar_one()

    async def get_fdc_conversation_by_restaurant(self, restaurant_id: UUID) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.restaurant_id == restaurant_id,
                Conversation.is_platform_chat.is_(True)))
        return result.scalar_one_or_none()