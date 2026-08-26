from ..repositories.authentication_repository import AuthenticationRepository
from ..schemas.schema import LoginSchema, RegisterIdentitySchema, RegisterRequestDTO, AddressResponseDTO
from ..security.password.password import hash_password, verify_password
from ..security.jwt.jwt import create_access_token
from datetime import date
from ..model.identity_model import IdentityRole, Identity
from ..exceptions.exceptions import PasswordError, LoginError


def send_new_user_dto(identity_id: str,
                     name : str,
                     surname : str,
                     email: str,
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

def send_address(city: str, postal_code : int, street : str, house : int, apartment : int) -> AddressResponseDTO:
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

    async def find_by_email(self, email : str) -> Identity:
        identity = await self.authentication_repository.get_by_email(email)
        if identity is None:
            raise LoginError("Such user was not found")
        return identity

    async def verify_credentials(self, email : str, password : str) -> Identity | None:
        identity = await self.find_by_email(email)
        if verify_password(password, identity.password_hash):
            return identity
        else:
            raise PasswordError("You entered invalid password")

    async def login(self, data : LoginSchema) -> str | None:
        identity = await self.verify_credentials(data.email, data.password)
        token = create_access_token(identity.id, identity.role)
        return token

    async def create_identity(self, email : str, password : str) -> RegisterIdentitySchema:
        return await self.authentication_repository.create_identity(email, hash_password(password))


