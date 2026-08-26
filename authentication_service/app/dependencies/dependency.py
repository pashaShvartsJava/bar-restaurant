from ..repositories.authentication_repository import AuthenticationRepository
from ..services.authentication_service import AuthenticationService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

def get_service_dependency(db : Session = Depends(get_db)):
    return AuthenticationService(AuthenticationRepository(db))