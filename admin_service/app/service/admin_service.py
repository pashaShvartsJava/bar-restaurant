from uuid import UUID

from ..repository.admin_repository import AdminRepository
from ..model.admin import Admin
from typing import List
from ..schema.admin import AdminRegistrationDTO, AdminUpdateDTO, AdminRegistrationForm


class AdminService:

    def __init__(self, admin_repository : AdminRepository):
        self.admin_repository = admin_repository

    async def find_by_id(self, id : int) -> Admin:
        return await self.admin_repository.get_by_id(id)

    async def find_all_admins(self) -> List[Admin]:
        return await self.admin_repository.get_all()

    async def fins_by_name(self, admin_name : str):
        return await self.admin_repository.get_by_name(admin_name)

    async def create_new_admin(self, adminDTO : AdminRegistrationDTO) -> AdminRegistrationDTO:
        return await self.admin_repository.create_admin(adminDTO)

    async def update_admin(self, updated_admin_id : int, updated_admin : AdminUpdateDTO) -> AdminUpdateDTO:
        return await self.admin_repository.update_admin(updated_admin_id, updated_admin)

    async def delete_admin(self, delete_admin_id : int) -> Admin:
        return await self.admin_repository.delete_admin(delete_admin_id)

    async def add_new_admin(self, admin_form : AdminRegistrationForm, identity_id : UUID):
        return await self.admin_repository.add_new_admin(admin_form, identity_id)
