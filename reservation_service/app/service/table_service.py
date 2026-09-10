from uuid import UUID

from ..repository.table_repository import TableRepository
from typing import List

class TableService:

    def __init__(self, table_repository : TableRepository):
        self.table_repository = table_repository

    async def find_all_tables(self):
        return await self.table_repository.get_all_tables()

    async def create_table(self, table_number : int, capacity : int):
        return await self.table_repository.create_table(table_number, capacity)