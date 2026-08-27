from ..model.address_model import Address
from ..schema.AdressSchema import AddressResponseDTO
from sqlalchemy.ext.asyncio import AsyncSession


class AddressRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def create_address(self, addressDTO : AddressResponseDTO) -> Address:
        new_address = Address(
            city=addressDTO.city,
            postal_code=addressDTO.postal_code,
            street=addressDTO.street,
            house=addressDTO.house,
            apartment=addressDTO.apartment
        )
        self.db.add(new_address)
        await self.db.commit()
        await self.db.refresh(new_address)
        return new_address