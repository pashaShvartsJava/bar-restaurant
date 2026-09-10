from ..repository.table_repository import TableRepository
from ..service.table_service import TableService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_table_service_dependency(db : AsyncSession = Depends(get_db)):
    return TableService(TableRepository(db))