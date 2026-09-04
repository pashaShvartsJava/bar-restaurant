from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..model.admin import Admin
from ..schema.admin import AdminRegistrationDTO, AdminUpdateDTO
from sqlalchemy import or_

class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Admin]:
        result = await self.db.execute(select(Admin))
        return result.scalars().all()

    async def get_by_id(self, id: int) -> Optional[Admin]:
        result = await self.db.execute(select(Admin).where(Admin.id == id))
        return result.scalar_one_or_none()

    async def get_by_name(self, admin_name: str) -> Optional[Admin]:
        result = await self.db.execute(
            select(Admin).where(or_(Admin.name == admin_name,Admin.surname == admin_name)))
        return result.scalar_one_or_none()

    async def create_admin(self, admin: AdminRegistrationDTO):
        new_admin = Admin(identity_id=admin.identity_id,
                          name = admin.name,
                          surname = admin.surname,
                          birthday=admin.birthday,
                          phone = admin.phone)
        self.db.add(new_admin)
        await self.db.commit()
        await self.db.refresh(new_admin)
        return new_admin

    async def update_admin(self, updated_admin_id: int, updated_admin: AdminUpdateDTO) -> Admin:
        admin = await self.get_by_id(updated_admin_id)
        admin.name = updated_admin.name
        admin.surname = updated_admin.surname
        admin.birthday = updated_admin.birthday
        admin.phone = updated_admin.phone
        admin.role = updated_admin.role
        await self.db.commit()
        await self.db.refresh(admin)
        return admin

    async def delete_admin(self, deleted_admin_id : int) -> Admin:
        old_admin = await self.get_by_id(deleted_admin_id)
        await self.db.delete(old_admin)
        await self.db.commit()
        return old_admin

