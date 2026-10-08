from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import selectinload, with_loader_criteria

from ..models import Reservation
from ..models.table import Table

class TableRepository:

    def __init__(self, db : AsyncSession):
        self.db = db

    async def get_table_by_id(self, table_id : int):
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Table).options(selectinload(Table.reservations),
                                  with_loader_criteria(Reservation, Reservation.reservation_start >= now)).where(Table.id == table_id))
        return result.scalar_one_or_none()

    async def get_all_tables(self):
        result = await self.db.execute(select(Table).order_by(Table.table_number.asc()))
        return result.scalars().all()

    async def create_table(self, table_number: int, capacity: int):
        new_table = Table(table_number=table_number, capacity=capacity)
        self.db.add(new_table)
        await self.db.commit()
        await self.db.refresh(new_table)

    async def get_free_table(self, people_amount: int, requested_datetime: datetime) -> dict[Table, int | None]:
        result = await self.db.execute(
            select(Table)
            .options(selectinload(Table.reservations))
            .where(Table.capacity >= people_amount)
        )
        tables = result.scalars().all()
        requested_datetime = requested_datetime.astimezone(timezone.utc)
        data = {}
        for table in tables:
            future_reservations = [
                reservation.reservation_start for reservation in table.reservations
                if reservation.reservation_start > requested_datetime
            ]
            if any(reservation.reservation_start <= requested_datetime <= reservation.reservation_end for reservation in table.reservations):
                continue
            next_reservation = min(future_reservations, default=None)
            if next_reservation is None:
                data[table] = None
            else:
                data[table] = int((next_reservation - requested_datetime).total_seconds() / 60)
        return dict(sorted(data.items(), key=lambda item: item[1] if item[1] is not None else float("inf"), reverse=True)[:1])
