from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from datetime import datetime, timezone
from ..model.user_model import User
from ..schema.user_schema import RegisterResponseDTO, UserEditSchema
from ..schema.address_schema import AddressResponseDTO
from uuid import UUID

class UserRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_by_identity_id(self, identity_id : UUID) -> User:
        result = await self.db.execute(select(User).options(selectinload(User.address)).where(User.identity_id==identity_id))
        return result.scalar_one_or_none()

    async def create_user(self, registerDTO : RegisterResponseDTO, addressDTO : AddressResponseDTO) -> User:
        new_user = User(
            identity_id=registerDTO.identity_id,
            name=registerDTO.name,
            surname=registerDTO.surname,
            email=registerDTO.email,
            birthday=registerDTO.birthday,
            phone=registerDTO.phone,
            role=registerDTO.role,
            address_id=addressDTO.id
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def update_user(self, user : User):
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user : User):
        await self.db.delete(user)
        await self.db.commit()

