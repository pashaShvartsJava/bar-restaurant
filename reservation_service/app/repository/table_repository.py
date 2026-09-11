from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from ..models.table import Table

class TableRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_table_by_id(self, table_id : int):
        result = await self.db.execute(select(Table).options(selectinload(Table.reservations)).where(Table.id==table_id))
        return result.scalar_one_or_none()

    async def get_all_tables(self):
        result = await self.db.execute(select(Table))
        return result.scalars().all()

    async def create_table(self, table_number: int, capacity: int):
        new_table = Table(table_number=table_number, capacity=capacity)
        self.db.add(new_table)
        await self.db.commit()
        await self.db.refresh(new_table)