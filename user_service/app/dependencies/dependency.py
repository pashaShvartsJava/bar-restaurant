from ..repositories.user_repository import UserRepository
from ..services.user_service import UserService
from ..repositories.address_repository import AddressRepository
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_service_dependency(db : AsyncSession = Depends(get_db)):
    return UserService(UserRepository(db), AddressRepository(db))