from datetime import datetime, timezone
from ..models.message import Message

from sqlalchemy.ext.asyncio import AsyncSession


class MessageRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, conversation_id: int, sender_id: int, sender_role, text: str) -> Message:
        now = datetime.now(timezone.utc)
        new_message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_role=sender_role,
            text=text,
            created_at=now
        )
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)
        return new_message