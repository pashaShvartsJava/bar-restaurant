from ..repository.table_repository import TableRepository
from ..service.table_service import TableService
from ..repository.reservation_repository import ReservationRepository
from ..service.reservation_service import ReservationService
from ..repository.table_session_repository import TableSessionRepository
from ..service.table_session_service import TableSessionService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_table_service_dependency(db : AsyncSession = Depends(get_db)):
    return TableService(TableRepository(db))

def get_table_session_service_dependency(db : AsyncSession = Depends(get_db)):
    return TableSessionService(TableSessionRepository(db), TableRepository(db))

def get_reservation_service_dependency(db : AsyncSession = Depends(get_db)):
    return ReservationService(ReservationRepository(db), TableRepository(db))