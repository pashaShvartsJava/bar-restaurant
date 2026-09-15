from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.conversation import Conversation
from sqlalchemy import or_, select
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

    async def take_conversation_by_admin(self, admin_id : UUID, conversation : Conversation):
        conversation.admin_id = admin_id
        await self.db.commit()
        await self.db.refresh(conversation)

    async def free_conversation(self, conversation_id : int):
        conversation = await self.get_conversation_by_id(conversation_id)
        conversation.admin_id = None
        await self.db.commit()
        await self.db.refresh(conversation)
