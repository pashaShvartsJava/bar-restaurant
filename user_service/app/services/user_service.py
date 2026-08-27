from ..repositories.user_repository import UserRepository
from ..repositories.address_repository import AddressRepository
from ..model.user_model import User
from ..schema.AdressSchema import AddressResponseDTO
from ..schema.user_schema import RegisterResponseDTO

class UserService:

    def __init__(self, user_repository : UserRepository, address_repository : AddressRepository ):
        self.user_repository = user_repository
        self.address_repository = address_repository

    async def find_by_identity_id(self, identity_id : int) -> User:
        return await self.user_repository.get_by_identity_id(identity_id)

    async def create_user(self, registerDTO : RegisterResponseDTO, addressDTO : AddressResponseDTO) -> User:
        accepted_address = await self.address_repository.create_address(addressDTO)
        return await self.user_repository.create_user(registerDTO, accepted_address)