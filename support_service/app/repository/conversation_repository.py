from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.conversation import Conversation
from sqlalchemy import or_, select
from ..security.role.role import IdentityRole


class ConversationRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_conversation_by_id(self, conversation_id : int) -> Conversation:
        result = await self.db.execute(select(Conversation).where(Conversation.id==conversation_id))
        return result.scalar_one_or_none()

    async def get_conversation_by_identity_id(self, identity_id):
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

    async def create_admin_conversation(self, identity_id, user_id):
        now = datetime.now(timezone.utc)
        new_conversation = Conversation(
            user_id=user_id,
            admin_id=identity_id,
            created_at=now
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)
