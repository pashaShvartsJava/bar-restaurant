from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..security.password.password import hash_password

from ..model.identity_model import Identity
from uuid import UUID


class AuthenticationRepository:

    def __init__ (self, db : AsyncSession):
        self.db = db

################################################
    # authentication process #
################################################

    async def get_by_email(self, email : str) -> Identity:
        result = await self.db.execute(select(Identity).where(Identity.email == email))
        return result.scalar_one_or_none()


#################################################
        # registration process #
#################################################

    async def create_identity(self, email : str, hashed_password : str) -> Identity:
        new_identity = Identity(
            email = email,
            password_hash = hashed_password
        )
        self.db.add(new_identity)
        await self.db.commit()
        await self.db.refresh(new_identity)
        return new_identity

    async def get_by_identity(self, identity_id : UUID) -> Identity:
        result = await self.db.execute(select(Identity).where(Identity.id == identity_id))
        return result.scalar_one_or_none()

    async def update_password(self, identity_id : UUID, new_password : str):
        identity = await self.get_by_identity(identity_id)
        identity.password_hash = hash_password(new_password)
        await self.db.commit()
        await self.db.refresh(identity)

    async def update_email(self, identity : Identity, new_email : str):
        identity.email = new_email
        await self.db.commit()
        await self.db.refresh(identity)

    async def delete_identity(self, identity_id : UUID):
        identity = await self.get_by_identity(identity_id)
        await self.db.delete(identity)
        await self.db.commit()
