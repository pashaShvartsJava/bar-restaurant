from datetime import datetime
from uuid import UUID

from ..repository.table_repository import TableRepository
from typing import List

class TableService:

    def __init__(self, table_repository : TableRepository):
        self.table_repository = table_repository

    async def find_all_tables(self, restaurant_id : UUID):
        return await self.table_repository.get_all_tables(restaurant_id)

    async def create_table(self, table_number : int, capacity : int, restaurant_id : UUID):
        return await self.table_repository.create_table(table_number, capacity, restaurant_id)

    async def get_table_by_id(self, table_id : int, restaurant_id : UUID):
        return await self.table_repository.get_table_by_id(table_id, restaurant_id)

    async def get_free_table(self, people_amount: int, requested_datetime: datetime, restaurant_d : UUID):
        return await self.table_repository.get_free_table(people_amount, requested_datetime, restaurant_d)

    async def find_all_available_tables(self, restaurant_id : UUID):
        return await self.table_repository.find_all_available_tables(restaurant_id)