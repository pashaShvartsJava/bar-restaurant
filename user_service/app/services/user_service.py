from ..repositories.user_repository import UserRepository
from ..model.user_model import User
from ..schema.AdressSchema import AddressResponseDTO
from ..schema.user_schema import RegisterResponseDTO

class UserService:

    def __init__(self, repository : UserRepository):
        self.repository = repository

    def find_by_identity_id(self, identity_id : int) -> User:
        return self.repository.get_by_identity_id(identity_id)

    def create_user(self, registerDTO : RegisterResponseDTO, addressDTO : AddressResponseDTO) -> User:
        return self.repository.create_user(registerDTO, addressDTO)