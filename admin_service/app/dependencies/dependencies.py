from admin_service.app.repository.admin_repository import AdminRepository
from admin_service.app.service.admin_service import AdminService
from admin_service.app.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

def get_service_dependency(db : Session = Depends(get_db)):
    return AdminService(AdminRepository(db))