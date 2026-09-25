from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.guest_customers import GuestCustomer
from ..schema.delivery_address_schema import GuestCustomerDTO


class GuestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_guest_order(self, data : GuestCustomerDTO, client_id : UUID) -> GuestCustomer:
        new_guest = GuestCustomer(
            client_id=client_id,
            name=data.name,
            surname=data.surname,
            email=data.email,
            birthday=data.birthday,
            phone=data.phone
        )
        self.db.add(new_guest)
        await self.db.commit()
        await self.db.refresh(new_guest)
        return new_guest