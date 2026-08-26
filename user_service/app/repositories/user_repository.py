from sqlalchemy.orm import Session

from ..model.user_model import User
from ..schema.user_schema import RegisterResponseDTO
from ..schema.AdressSchema import AddressResponseDTO

class UserRepository:

    def __init__(self, db : Session):
        self.db = db

    def get_by_identity_id(self, identity_id : int) -> User:
        return self.db.query(User).filter(User.identity_id==identity_id)

    def create_user(self, registerDTO : RegisterResponseDTO, addressDTO : AddressResponseDTO) -> User:
        accepted_address = self.address_repository.create_address(addressDTO)
        new_user = User(
            name=registerDTO.name,
            surname=registerDTO.surname,
            email=registerDTO.email,
            birthday=registerDTO.birthday,
            phone=registerDTO.phone,
            role=registerDTO.role,
            address_id=accepted_address.id
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

