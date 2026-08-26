from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..model.identity_model import Identity


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
