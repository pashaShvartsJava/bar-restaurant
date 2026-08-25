from ..repositories.user_repository import UserRepository
from ..services.user_service import UserService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

def get_service_dependency(db : Session = Depends(get_db)):
    return UserService(UserRepository(db))