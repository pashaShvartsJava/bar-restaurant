from datetime import datetime, date, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Table
from ..models.reservation import Reservation

class ReservationRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_all_reservations(self):
        result = await self.db.execute(select(Reservation).options(selectinload(Reservation.table)).order_by(Reservation.reservation_start.desc()))
        return result.scalars().all()

    async def create_reservation(self, table_id : int, name : str, surname : str, phone : str,
                                 reservation_start : datetime, reservation_end : datetime):
        new_reservation = Reservation(
            table_id=table_id,
            name=name,
            surname=surname,
            phone=phone,
            reservation_start=reservation_start,
            reservation_end=reservation_end
        )
        self.db.add(new_reservation)
        await self.db.commit()
        await self.db.refresh(new_reservation)

    async def get_reservation_by_id(self, reservation_id : int):
        result = await self.db.execute(select(Reservation).where(Reservation.id==reservation_id))
        return result.scalar_one_or_none()

    async def cancel_reservation(self, reservation_id : int):
        cancelled_reservation = await self.get_reservation_by_id(reservation_id)
        await self.db.delete(cancelled_reservation)
        await self.db.commit()

    async def get_reservation_by_search(self, reservation_number : UUID, name : str, surname : str):
        query = select(Reservation).options(selectinload(Reservation.table)).order_by(Reservation.reservation_start.desc())
        if reservation_number is not None:
            query = query.where(Reservation.reservation_number==reservation_number)
        if name is not None:
            query = query.where(Reservation.name.ilike(f"%{name}%"))
        if surname is not None:
            query = query.where(Reservation.surname.ilike(f"%{surname}%"))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def filter_reservations(self, date : date, status : str, table_number : int):
        query = select(Reservation).options(selectinload(Reservation.table)).order_by(Reservation.reservation_start.desc())
        now = datetime.now(timezone.utc)
        if date is not None:
            query = query.where(func.date(Reservation.reservation_start) == date)
        if status == "active":
            query = query.where(Reservation.reservation_end>=now)
        if status == "finished":
            query = query.where(Reservation.reservation_end<now)
        if table_number is not None:
            query = query.join(Reservation.table).where(Table.table_number==table_number)
        result = await self.db.execute(query)
        return result.scalars().all()
