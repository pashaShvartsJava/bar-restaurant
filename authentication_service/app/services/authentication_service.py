from pydantic import EmailStr
from watchfiles import awatch

from ..repositories.authentication_repository import AuthenticationRepository
from ..schemas.admin_schema import IdentityEdit, AddAdminRequest
from ..schemas.schema import LoginSchema, RegisterIdentitySchema, RegisterRequestDTO, AddressResponseDTO
from ..security.password.password import hash_password, verify_password
from ..security.jwt.jwt import create_access_token
from datetime import date
from ..model.identity_model import IdentityRole, Identity, Status
from ..exceptions.exceptions import PasswordError, LoginError, InvalidCredentialsError, EmailError
from uuid import UUID


def send_new_user_dto(identity_id: UUID,
                     name : str,
                     surname : str,
                     email: EmailStr,
                     birthday : date,
                     phone : str,
                     role : IdentityRole) -> RegisterRequestDTO:
    new_user = RegisterRequestDTO(
        identity_id=identity_id,
        name=name,
        surname=surname,
        email=email,
        birthday=birthday,
        phone=phone,
        role=role
    )
    return new_user

def send_address(city: str, postal_code : str, street : str, house : int, apartment : int) -> AddressResponseDTO:
    created_address = AddressResponseDTO(
        city=city,
        postal_code=postal_code,
        street=street,
        house=house,
        apartment=apartment
    )
    return created_address

class AuthenticationService:

    def __init__(self, authentication_repository : AuthenticationRepository):
        self.authentication_repository = authentication_repository

    async def find_by_identity(self, identity_id : UUID) -> Identity:
        return await self.authentication_repository.get_by_identity(identity_id)

    async def find_by_email(self, email : EmailStr) -> Identity | None:
        identity = await self.authentication_repository.get_by_email(email)
        return identity

    async def verify_credentials(self, email : EmailStr, password : str) -> Identity | None:
        identity = await self.find_by_email(email)
        if identity is None or not verify_password(password, identity.password_hash):
            raise InvalidCredentialsError("Пользователь не найден или неверный пароль")
        else:
            return identity

    async def login(self, data : LoginSchema) -> str | None:
        identity = await self.verify_credentials(data.email, data.password)
        token = create_access_token(identity.id, identity.role, identity.status)
        return token

    async def create_identity(self, email : EmailStr, password : str):
        return await self.authentication_repository.create_identity(email, hash_password(password))

    async  def update_password(self, identity_id : UUID, new_password : str):
        return await self.authentication_repository.update_password(identity_id, new_password)

    async def update_email(self, identity : Identity, new_email : EmailStr):
        return await self.authentication_repository.update_email(identity, new_email)

    async def delete_identity(self, identity_id : UUID):
        return await self.authentication_repository.delete_identity(identity_id)

    async def create_admin_identity(self, email : EmailStr, password : str):
        return await self.authentication_repository.create_admin_identity(email, hash_password(password))

    async def verify_registration_key(self, key : str) -> str | None:
        return await self.authentication_repository.verify_registration_key(key)

    async def verify_authentication_key(self, key : str) -> str | None:
        return await self.authentication_repository.verify_authentication_key(key)

    async def update_status_identity(self, identity : Identity, status : Status):
        return await self.authentication_repository.update_status_identity(identity, status)

    async def update_identity_role(self, identity : Identity, role : IdentityRole):
        return await self.authentication_repository.update_identity_role(identity, role)

    async def update_identity(self, identity : Identity, data : IdentityEdit):
        return await self.authentication_repository.update_identity(identity, data)

    async def add_new_identity(self, data : AddAdminRequest):
        hashed_password = hash_password(data.password)
        data.password = hashed_password
        return await self.authentication_repository.add_new_identity(data)




