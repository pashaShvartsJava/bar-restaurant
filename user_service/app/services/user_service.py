import jwt
from watchfiles import awatch

from ..repositories.user_repository import UserRepository
from ..repositories.address_repository import AddressRepository
from ..model.user_model import User
from ..schema.address_schema import AddressResponseDTO
from ..schema.user_schema import RegisterResponseDTO, UserEditSchema, PasswordResponse
from uuid import UUID


class UserService:

    def __init__(self, user_repository : UserRepository, address_repository : AddressRepository ):
        self.user_repository = user_repository
        self.address_repository = address_repository

    async def find_by_identity_id(self, identity_id : UUID) -> User:
        return await self.user_repository.get_by_identity_id(identity_id)

    async def create_user(self, registerDTO : RegisterResponseDTO, addressDTO : AddressResponseDTO) -> User:
        accepted_address = await self.address_repository.create_address(addressDTO)
        return await self.user_repository.create_user(registerDTO, accepted_address)

    async def update_user(self, user: User, data: UserEditSchema):

        if data.name is not None:
            user.name = data.name

        if data.surname is not None:
            user.surname = data.surname

        if data.birthday is not None:
            user.birthday = data.birthday

        if data.phone is not None:
            user.phone = data.phone

        if data.email is not None:
            user.email = data.email

        if data.city is not None:
            user.address.city = data.city

        if data.street is not None:
            user.address.street = data.street

        if data.postal_code is not None:
            user.address.postal_code = data.postal_code

        if data.house is not None:
            user.address.house = data.house

        if data.apartment is not None:
            user.address.apartment = data.apartment

        return await self.user_repository.update_user(user)

    async def delete_user(self, user : User):
        return await self.user_repository.delete_user(user)

    async def find_all_users(self):
        return await self.user_repository.get_all_users()

