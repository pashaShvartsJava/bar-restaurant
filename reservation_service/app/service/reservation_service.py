from datetime import datetime, date
from ..repository.reservation_repository import ReservationRepository
from ..repository.table_repository import TableRepository
from uuid import UUID

class ReservationService:

    def __init__(self, reservation_repository : ReservationRepository, table_repository : TableRepository):
        self.reservation_repository = reservation_repository
        self.table_repository = table_repository

    async def get_all_reservations(self):
        return await self.reservation_repository.get_all_reservations()

    async def create_reservation(self, table_id : int, name : str, surname : str, phone : str,
                                 reservation_start : datetime, reservation_end : datetime):
        table = await self.table_repository.get_table_by_id(table_id)
        if not table.reservations:
            return await self.reservation_repository.create_reservation(table_id, name, surname, phone, reservation_start, reservation_end)
        else:
            for reservation in table.reservations:
                if reservation_start < reservation.reservation_end and reservation_end > reservation.reservation_start:
                    raise ValueError("Бронирование на это время уже занято")
        return await self.reservation_repository.create_reservation(table_id, name, surname, phone, reservation_start, reservation_end)

    async def cancel_reservation(self, reservation_id : int):
        return await self.reservation_repository.cancel_reservation(reservation_id)

    async def get_reservation_by_search(self, reservation_number : UUID, name : str, surname : str):
        return await self.reservation_repository.get_reservation_by_search(reservation_number, name, surname)

    async def filter_reservations(self, date : date, status : str, table_number : int):
        return await self.reservation_repository.filter_reservations(date, status, table_number)
