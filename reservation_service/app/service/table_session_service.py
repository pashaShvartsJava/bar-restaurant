from uuid import UUID

from requests import session

from ..models.table import TableStatus, Table
from ..repository.table_repository import TableRepository
from ..repository.table_session_repository import TableSessionRepository
from typing import List

class TableSessionService:

    def __init__(self, table_session_repository : TableSessionRepository, table_repository : TableRepository):
        self.table_session_repository = table_session_repository
        self.table_repository = table_repository

    async def get_table_by_id(self, id : int, restaurant_id : UUID) -> Table:
        return await self.table_repository.get_table_by_id(id, restaurant_id)

    async def start_session(self, id : int, restaurant_id : UUID):
        table = await self.get_table_by_id(id, restaurant_id)
        if table.status == TableStatus.TAKEN:
            raise ValueError("Impossible to take a table")
        return await self.table_session_repository.start_session(id, table, restaurant_id)

    async def end_session(self, table_id : int, restaurant_id : UUID):
        session = await self.table_session_repository.get_session_by_table_id(table_id, restaurant_id)
        if session is None:
            raise ValueError("Active session was not found")
        table = await self.get_table_by_id(table_id, restaurant_id)
        table.status = TableStatus.UNTAKEN
        return await self.table_session_repository.end_session(session)