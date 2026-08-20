from sqlalchemy.orm import Session
from typing import List, Optional
from ..model.admin import Admin
from ..schema.admin import AdminRegistrationDTO, AdminUpdateDTO
from sqlalchemy import or_

class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Admin]:
        return self.db.query(Admin).all()

    def get_by_id(self, id: int) -> Optional[Admin]:
        return self.db.query(Admin).get(id)

    def get_by_name(self, admin_name: str) -> Optional[Admin]:
        return self.db.query(Admin).filter(or_(Admin.name == admin_name, Admin.surname == admin_name)).first()

    def create_admin(self, admin: AdminRegistrationDTO):
        new_admin = Admin(name = admin.name,
                          surname = admin.surname,
                          birthday=admin.birthday,
                          phone = admin.phone,
                          email=admin.email,
                          password = admin.password,
                          role = admin.role)
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        return new_admin

    def update_admin(self, updated_admin_id: int, updated_admin: AdminUpdateDTO) -> Admin:
        admin = self.get_by_id(updated_admin_id)
        admin.name = updated_admin.name
        admin.surname = updated_admin.surname
        admin.birthday = updated_admin.birthday
        admin.phone = updated_admin.phone
        admin.email = updated_admin.email
        admin.role = updated_admin.role
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def delete_admin(self, deleted_admin_id : int) -> Admin:
        old_admin = self.get_by_id(deleted_admin_id)
        self.db.delete(old_admin)
        self.db.commit()
        return old_admin

