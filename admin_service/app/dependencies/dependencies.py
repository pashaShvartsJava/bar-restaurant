from ..repository.admin_repository import AdminRepository
from ..service.admin_service import AdminService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return AdminService(AdminRepository(db))