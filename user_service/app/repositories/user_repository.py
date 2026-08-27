from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..model.user_model import User
from ..schema.user_schema import RegisterResponseDTO
from ..schema.AdressSchema import AddressResponseDTO

class UserRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_by_identity_id(self, identity_id : int) -> User:
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

