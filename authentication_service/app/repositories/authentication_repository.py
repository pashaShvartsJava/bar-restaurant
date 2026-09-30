import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..model.confirmation_token_model import EmailVerificationToken
from ..model.identity_model import IdentityRole, Status
from ..model.key_model import Key
from ..model.outbox_email_verification_events import OutboxEmailVerificationEvents
from ..model.update_password_email_token_model import UpdatePasswordEmailToken
from ..schemas.admin_schema import IdentityEdit, AddAdminRequest
from ..security.password.password import hash_password

from ..model.identity_model import Identity
from uuid import UUID

async def generate_verification_hashed_token() -> str:
    token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return hashed_token


class AuthenticationRepository:

    def __init__ (self, db : AsyncSession):
        self.db = db

    async def get_all_identities(self):
        result = await self.db.execute(select(Identity).where(Identity.role == IdentityRole.USER))
        return result.scalars().all()

################################################
    # authentication process #
################################################

    async def get_by_email(self, email : EmailStr) -> Identity | None:
        result = await self.db.execute(select(Identity).where(Identity.email == email))
        return result.scalar_one_or_none()


#################################################
        # registration process #
#################################################

    async def create_identity(self, email : EmailStr, hashed_password : str) -> Identity:
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode("utf-8")).hexdigest()
        async with self.db.begin():
            new_identity = Identity(
                email=email,
                password_hash=hashed_password
            )
            self.db.add(new_identity)
            await self.db.flush()
            await self.create_verification_token(new_identity.id, hashed_token)
            await self.create_outbox_event_email_verification(event_id=str(uuid.uuid4()), email=new_identity.email, token=token)
        return new_identity

    async def create_admin_identity(self, email : EmailStr, hashed_password : str) -> Identity:
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode("utf-8")).hexdigest()
        async with self.db.begin():
            new_identity = Identity(
                email=email,
                password_hash=hashed_password,
                role=IdentityRole.ADMIN
            )
            self.db.add(new_identity)
            await self.db.flush()
            await self.create_verification_token(new_identity.id, hashed_token)
            await self.create_outbox_event_email_verification(str(uuid.uuid4()), new_identity.email, token)
        return new_identity

    async def get_by_identity(self, identity_id : UUID) -> Identity:
        result = await self.db.execute(select(Identity).where(Identity.id == identity_id))
        return result.scalar_one_or_none()

    async def update_password(self, identity_id : UUID, new_password : str):
        identity = await self.get_by_identity(identity_id)
        identity.password_hash = hash_password(new_password)
        await self.db.commit()
        await self.db.refresh(identity)

    async def update_email(self, identity : Identity, new_email : EmailStr):
        identity.email = new_email
        await self.db.commit()
        await self.db.refresh(identity)

    async def delete_identity(self, identity_id : UUID):
        identity = await self.get_by_identity(identity_id)
        if identity is None:
            raise HTTPException(status_code=404,detail="Пользователь не найден")
        await self.db.delete(identity)
        await self.db.commit()

    async def verify_registration_key(self, key : str) -> str | None:
        result = await self.db.execute(select(Key).where(Key.registration_key==key))
        return result.scalar_one_or_none()

    async def verify_authentication_key(self, key : str) -> str | None:
        result = await self.db.execute(select(Key).where(Key.authentication_key==key))
        return result.scalar_one_or_none()

    async def update_status_identity(self, identity : Identity, status : Status):
        identity.status = status
        await self.db.commit()
        await self.db.refresh(identity)

    async def update_identity_role(self, identity : Identity, role : IdentityRole):
        identity.role = role
        await self.db.commit()
        await self.db.refresh(identity)

    async def update_identity(self, identity : Identity, data : IdentityEdit):
        if data.email is not None:
            identity.email = data.email
        if data.role is not None:
            identity.role = data.role
        await self.db.commit()
        await self.db.refresh(identity)

    async def add_new_identity(self, data : AddAdminRequest):
        new_identity = Identity(id=data.identity_id, email=data.email, password_hash=data.password, role=data.role, status=Status.ACTIVE)
        self.db.add(new_identity)
        await self.db.commit()
        await self.db.refresh(new_identity)

    #################################################
    # verification email process #
    #################################################

    async def find_verification_token(self, hashed_token : str) -> EmailVerificationToken | None:
        result = await self.db.execute(select(EmailVerificationToken)
                                       .options(selectinload(EmailVerificationToken.identity))
                                       .where(EmailVerificationToken.token_hash==hashed_token))
        return result.scalar_one_or_none()

    async def create_verification_token(self, identity_id: UUID, hashed_token : str) -> EmailVerificationToken:
        new_token = EmailVerificationToken(
            identity_id=identity_id,
            token_hash=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        self.db.add(new_token)
        await self.db.flush()
        return new_token

    async def create_verify_change_password_token(self, identity_id: UUID) -> UpdatePasswordEmailToken:
        async with self.db.begin():
            token = secrets.token_urlsafe(32)
            hashed_token = hashlib.sha256(token.encode("utf-8")).hexdigest()
            new_token = UpdatePasswordEmailToken(
                identity_id=identity_id,
                token_hash=hashed_token,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            self.db.add(new_token)
            await self.db.flush()
            identity = await self.get_by_identity(identity_id)
            await self.create_outbox_event_change_password_verification(event_id=str(uuid.uuid4()),
                                                                        email=identity.email,
                                                                        token=token)
        await self.db.refresh(new_token)
        return new_token


    async def get_all_unpublished_events(self) -> List[OutboxEmailVerificationEvents]:
        result = await self.db.execute(select(OutboxEmailVerificationEvents).where(OutboxEmailVerificationEvents.published_at == None))
        return result.scalars().all()

    async def mark_event_as_published(self, event: OutboxEmailVerificationEvents):
        event.published_at = datetime.now(timezone.utc)
        await self.db.flush()



    async def create_outbox_event_email_verification(self, event_id : str, email : EmailStr, token : str) -> OutboxEmailVerificationEvents:
        found_event = await self.get_event_by_event_id(event_id)
        if found_event is not None:
            return found_event
        outbox_event = OutboxEmailVerificationEvents(
            event_type="EmailVerification",
            payload={
                "email": email,
                "token": str(token),
            },
            event_id=event_id
        )
        self.db.add(outbox_event)
        await self.db.flush()
        return outbox_event

    async def create_outbox_event_change_password_verification(self, event_id : str, email : EmailStr, token : str) -> OutboxEmailVerificationEvents:
        found_event = await self.get_event_by_event_id(event_id)
        if found_event is not None:
            return found_event
        outbox_event = OutboxEmailVerificationEvents(
            event_type="ChangePasswordVerification",
            payload={
                "email": email,
                "token": str(token),
            },
            event_id=event_id
        )
        self.db.add(outbox_event)
        await self.db.flush()
        return outbox_event

    async def get_event_by_event_id(self, event_id : str) -> OutboxEmailVerificationEvents | None:
        result = await self.db.execute(select(OutboxEmailVerificationEvents).where(OutboxEmailVerificationEvents.event_id==event_id))
        return result.scalar_one_or_none()

    async def find_identity_by_token(self, hashed_token) -> Identity | None:
        result = await self.db.execute(select(EmailVerificationToken).options(selectinload(EmailVerificationToken.identity))
        .where(EmailVerificationToken.token_hash == hashed_token, EmailVerificationToken.used_at.is_(None)))
        return result.scalar_one_or_none()

    async def verify_email(self, hashed_token: str):
        async with self.db.begin():
            found_token = await self.find_verification_token(hashed_token)
            print("FOUND TOKEN::::::: ", found_token)
            now = datetime.now(timezone.utc)
            if found_token is not None and found_token.expires_at > now:
                found_token.used_at = now
            found_identity : Identity = found_token.identity
            found_identity.verified_email = True
        await self.db.refresh(found_identity)
