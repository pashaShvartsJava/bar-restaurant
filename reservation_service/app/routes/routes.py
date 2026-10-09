import secrets
from datetime import datetime, timezone, date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Request, Form, HTTPException, Response
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pydantic import EmailStr
from starlette.responses import RedirectResponse, JSONResponse
from starlette.templating import Jinja2Templates
from fastapi.params import Depends

from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_table_service_dependency, get_table_session_service_dependency, get_reservation_service_dependency
from ..service.table_service import TableService
from ..service.table_session_service import TableSessionService
from ..service.reservation_service import ReservationService
from ..config.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
COOKIE_SECRET_KEY = settings.cookie_secret_key
serializer = URLSafeTimedSerializer(COOKIE_SECRET_KEY)

async def verify_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403)

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
    await verify_csrf(request)
    await table_service.create_table(table_number, capacity)
    return RedirectResponse(url="/tables", status_code=303)

@router.post("/tables/start_session/{table_id}")
async def take_table(request : Request, table_id : int,  service : TableSessionService = Depends(get_table_session_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    await service.start_session(table_id)
    return RedirectResponse(url="/tables", status_code=303)

@router.post("/tables/end_session/{table_id}")
async def take_table(request : Request, table_id : int,  service : TableSessionService = Depends(get_table_session_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
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
                             reservation_service : ReservationService = Depends(get_reservation_service_dependency),
                             table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    reservation_start = reservation_start.replace(tzinfo=timezone.utc)
    reservation_end = reservation_end.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if reservation_start.date() != reservation_end.date() or reservation_start>=reservation_end\
            or reservation_start <= now:
        table = await table_service.get_table_by_id(table_id)
        return templates.TemplateResponse( "add_reservation.html",
                                           { "request": request,
                                             "table": table,
                                             "error": "Даты указаны некорректно. Бронирование должно быть в будущем и начинаться раньше окончания." },
                                             status_code=400 )
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
    await verify_csrf(request)
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

@router.get("/tables/get_free_table")
async def find_free_table(request : Request):
    return templates.TemplateResponse("get_free_table.html", {"request" : request})

@router.post("/tables/get_free_table")
async def find_free_table(response : Response,
                          people_amount : int = Form(..., lt=7),
                          requested_datetime : datetime = Form(),
                          service : TableService = Depends(get_table_service_dependency)):
    free_table = await service.get_free_table(people_amount, requested_datetime)
    if not free_table:
        raise HTTPException(status_code=409, detail="К сожалению, все столики уже заняты. Попробуйте выбрать другое время")
    table, minutes = next(iter(free_table.items()))
    if minutes is None:
        message = "После выбранного вами времени следующая бронь отсутствует"
    else:
        message = f"Учитывая выбранное вами время, столик будет свободен ещё {minutes} минут"
    token = serializer.dumps({
        "requested_datetime": requested_datetime.isoformat(),
        "table_id" : table.id,
        "minutes" : minutes
    })
    response.set_cookie(
        key="reservation_draft",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600,
        value=token
    )
    return {"success": True, "message": message}

@router.post("/tables/confirm_reservation")
async def confirm_reservation(request : Request,
                              phone_number: Annotated[str, Form(pattern=r"^\+?[1-9]\d{7,14}$")],
                              name : str = Form(..., min_length=2),
                              surname : str = Form(..., min_length=2),
                              email : EmailStr = Form(),
                              service : ReservationService = Depends(get_reservation_service_dependency)):
    token = request.cookies.get("reservation_draft")
    if not token:
        raise HTTPException(status_code=400, detail="Срок действия бронирования истёк. Повторите поиск столика.")
    try:
        data = serializer.loads(token, max_age=600)
    except BadSignature:
        raise HTTPException(status_code=405, detail="Некорректные данные поиска")
    except SignatureExpired:
        raise HTTPException(status_code=406, detail="Ошибка. Попробуйте перезайти на страницу заново и повторить операцию")
    requested_datetime = datetime.fromisoformat(data["requested_datetime"])
    if requested_datetime.tzinfo is None:
        requested_datetime = requested_datetime.replace(tzinfo=timezone.utc)
    else:
        requested_datetime = requested_datetime.astimezone(timezone.utc)
    table_id = data["table_id"]
    minutes = data["minutes"]
    reservation_end = None
    if minutes is None:
        reservation_end = requested_datetime + timedelta(hours=2)
    elif int(minutes) < 60:
        reservation_end = requested_datetime + timedelta(minutes=int(minutes))
    else:
        reservation_end = requested_datetime + timedelta(minutes=60)
    await service.create_reservation(table_id, name, surname, phone_number, requested_datetime, reservation_end, email)
    return {"success": True, "message": "Бронирование успешно подтверждено."}

