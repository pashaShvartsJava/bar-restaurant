from admin_service.repository.admin_repository import AdminRepository
from admin_service.model.admin import Admin
from typing import List
from admin_service.schema.admin import AdminRegistrationDTO

class AdminService:

    def __init__(self, admin_repository : AdminRepository):
        self.admin_repository = admin_repository

    def find_by_id(self, id : int) -> Admin:
        return self.admin_repository.get_by_id(id)

    def find_all_admins(self) -> List[Admin]:
        return self.admin_repository.get_all()

    def fins_by_name(self, admin_name : str):
        return self.admin_repository.get_by_name(admin_name)

    def create_new_admin(self, adminDTO : AdminRegistrationDTO) -> AdminRegistrationDTO:
        return self.admin_repository.create_admin(adminDTO)

    def update_admin(self, id : int, admin : Admin) -> Admin:
        return self.admin_repository.update_admin(id, admin)

    def delete_admin(self, id : int) -> Admin:
        return self.admin_repository.delete_admin(id)
