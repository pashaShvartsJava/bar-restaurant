from datetime import datetime, timezone, date
from uuid import UUID

from fastapi import APIRouter, Request, Form, HTTPException
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from fastapi.params import Depends

from ..models.table import TableStatus
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_table_service_dependency, get_table_session_service_dependency, get_reservation_service_dependency
from ..service.table_service import TableService
from ..service.table_session_service import TableSessionService
from ..service.reservation_service import ReservationService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/tables")
async def show_tables_page(request : Request, table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    tables = await table_service.find_all_tables()
    return templates.TemplateResponse("all_tables.html", {"request" : request, "tables" : tables})

@router.get("/tables/add_table")
async def add_table_page(request : Request):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    return templates.TemplateResponse("add_table.html", {"request" : request})

@router.post("/tables/add_table")
async def add_table(request : Request,
                    table_number : int = Form(..., min=1),
                    capacity : int = Form(..., min=1),
                    table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await table_service.create_table(table_number, capacity)
    return RedirectResponse(url="/tables", status_code=303)

@router.post("/tables/start_session/{table_id}")
async def take_table(request : Request, table_id : int,  service : TableSessionService = Depends(get_table_session_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await service.start_session(table_id)
    return RedirectResponse(url="/tables", status_code=303)

@router.post("/tables/end_session/{table_id}")
async def take_table(request : Request, table_id : int,  service : TableSessionService = Depends(get_table_session_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await service.end_session(table_id)
    return RedirectResponse(url="/tables", status_code=303)

@router.get("/tables/create_reservation")
async def create_reservation_page(request : Request, table_id : int, table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    table = await table_service.get_table_by_id(table_id)
    return templates.TemplateResponse("add_reservation.html", {"request" : request, "table" : table})

@router.post("/tables/create_reservation")
async def create_reservation(request : Request,
                             table_id : int = Form(...),
                             name : str = Form(..., min_length=2),
                             surname : str = Form(..., min_length=2),
                             phone : str = Form(..., ),
                             reservation_start : datetime = Form(...,),
                             reservation_end : datetime = Form(...,),
                             reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    reservation_start = reservation_start.replace(tzinfo=timezone.utc)
    reservation_end = reservation_end.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if reservation_start.date() != reservation_end.date() or reservation_start>=reservation_end\
            or reservation_start <= now:
        raise HTTPException(status_code=401, detail="Dates are not the same or dates are incorrect")
    await reservation_service.create_reservation(table_id, name, surname, phone, reservation_start, reservation_end)
    return RedirectResponse(url="/tables", status_code=303)

@router.get("/tables/reservations/history")
async def reservations_page(request : Request, reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    reservations = await reservation_service.get_all_reservations()
    return templates.TemplateResponse("all_reservations.html", {"request" : request, "reservations" : reservations, "now": datetime.now(timezone.utc)})

@router.post("/tables/reservations/cancel/{reservation_id}")
async def cancel_reservation(request : Request, reservation_id : int, reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await reservation_service.cancel_reservation(reservation_id)
    return RedirectResponse(url="/tables/reservations/history", status_code=303)

@router.get("/tables/reservations/history/search")
async def show_reservation(request : Request,
                           reservation_number : str | None = None,
                           name : str | None = None,
                           surname : str | None = None,
                           reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    reservation_uuid = None
    if reservation_number:
        reservation_uuid = UUID(reservation_number)
    reservations = await reservation_service.get_reservation_by_search(reservation_uuid, name, surname)
    return templates.TemplateResponse("all_reservations.html", {"request": request, "reservations": reservations,
                                                                "now": datetime.now(timezone.utc)})
@router.get("/tables/reservations/filtered_history")
async def filter_reservations(request : Request,
                              date : date | None = None,
                              status : str | None = None,
                              table_number : int | None = None,
                              reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    reservations = await reservation_service.filter_reservations(date, status, table_number)
    return templates.TemplateResponse("all_reservations.html", {"request": request, "reservations": reservations,
                                                                "now": datetime.now(timezone.utc)})