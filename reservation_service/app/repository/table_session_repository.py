from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import or_
from ..models.table import Table, TableStatus
from ..models.table_session import TableSession

class TableSessionRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_session_by_table_id(self, id : int) -> TableSession:
        result = await self.db.execute(select(TableSession).where(TableSession.table_id == id).where(TableSession.session_end.is_(None)))
        return result.scalar_one_or_none()

    async def start_session(self, table_id : int, table : Table):
        new_session = TableSession(table_id=table_id)
        table.status = TableStatus.TAKEN
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)

    async def get_session_by_id(self, session_id) -> TableSession:
        result = await self.db.execute(select(TableSession).where(TableSession.id==session_id))
        return result.scalar_one_or_none()

    async def end_session(self, old_session : TableSession):
        if old_session.session_end is not None:
            raise ValueError("This session is already finished")
        old_session.session_end = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(old_session)

