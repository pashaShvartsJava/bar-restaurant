from sqlalchemy.orm import Session
from typing import List, Optional
from ..model.admin import Admin
from ..schema.admin import AdminRegistrationCreate, AdminRegistrationUpdate

class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Admin]:
        return self.db.query(Admin).all()

    def get_by_id(self, id: int) -> Optional[Admin]:
        return self.db.query(Admin).get(id)

    def get_by_name(self, admin_name: str) -> Optional[Admin]:
        return self.db.query(Admin).filter(Admin.name == admin_name).first()

    def create_admin(self, admin: AdminRegistrationCreate):
        new_admin = Admin(name = admin.name, surname = admin.surname, birthday=admin.birthday,
                          phone = admin.phone, email=admin.email, password=admin.password)
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        return new_admin

    def update_admin(self, id: int, updated_admin: AdminRegistrationUpdate) -> Admin:
        admin = self.db.query(Admin).get(id)
        admin.name = updated_admin.name
        admin.surname = updated_admin.surname
        admin.birthday = updated_admin.birthday
        admin.phone = updated_admin.phone
        admin.email = updated_admin.email
        admin.password = updated_admin.password
        self.db.commit()
        self.db.refresh(admin)
        return admin

