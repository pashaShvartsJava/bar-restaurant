import secrets
from datetime import datetime, timezone, date, timedelta
from email.header import Header
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Request, Form, HTTPException, Response, Header
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pydantic import EmailStr
from starlette.responses import RedirectResponse, JSONResponse
from starlette.templating import Jinja2Templates
from fastapi.params import Depends

from ..security.internal_security import verify_internal_token
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_table_service_dependency, get_table_session_service_dependency, \
    get_reservation_service_dependency, get_restaurant_dependency
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

@router.get("/r/{slug}/tables")
async def show_tables_page(request : Request, slug : str, table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    tables = await table_service.find_all_tables(restaurant.id)
    return templates.TemplateResponse("all_tables.html", {"request" : request,
                                                          "tables" : tables,
                                                          "restaurant" : restaurant,
                                                          "slug" : slug})

@router.get("/r/{slug}/tables/add_table")
async def add_table_page(request : Request, slug : str):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    return templates.TemplateResponse("add_table.html", {"request" : request, "restaurant" : restaurant, "slug" : slug})

@router.post("/r/{slug}/tables/add_table")
async def add_table(request : Request,
                    slug : str,
                    table_number : int = Form(..., min=1),
                    capacity : int = Form(..., min=1),
                    table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant = await get_restaurant_dependency(slug)
    await table_service.create_table(table_number, capacity, restaurant.id)
    return RedirectResponse(url=f"/r/{slug}/tables", status_code=303)

@router.post("/r/{slug}/tables/start_session/{table_id}")
async def take_table(request : Request, slug : str, table_id : int,  service : TableSessionService = Depends(get_table_session_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant = await get_restaurant_dependency(slug)
    await service.start_session(table_id, restaurant.id)
    return RedirectResponse(url=f"/r/{slug}/tables", status_code=303)

@router.post("/r/{slug}/tables/end_session/{table_id}")
async def take_table(request : Request, slug : str, table_id : int,  service : TableSessionService = Depends(get_table_session_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant = await get_restaurant_dependency(slug)
    await service.end_session(table_id, restaurant.id)
    return RedirectResponse(url=f"/r/{slug}/tables", status_code=303)

@router.get("/r/{slug}/tables/create_reservation")
async def create_reservation_page(request : Request, slug : str, table_id : int, table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    table = await table_service.get_table_by_id(table_id, restaurant.id)
    return templates.TemplateResponse("add_reservation.html", {"request" : request,
                                                               "table" : table,
                                                               "slug" : slug,
                                                               "restaurant" : restaurant})

@router.post("/r/{slug}/tables/create_reservation")
async def create_reservation(request : Request,
                             slug : str,
                             table_id : int = Form(...),
                             name : str = Form(..., min_length=2),
                             surname : str = Form(..., min_length=2),
                             phone : str = Form(..., ),
                             reservation_start : datetime = Form(...,),
                             reservation_end : datetime = Form(...,),
                             reservation_service : ReservationService = Depends(get_reservation_service_dependency),
                             table_service : TableService = Depends(get_table_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant = await get_restaurant_dependency(slug)
    reservation_start = reservation_start.replace(tzinfo=timezone.utc)
    reservation_end = reservation_end.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if reservation_start.date() != reservation_end.date() or reservation_start>=reservation_end\
            or reservation_start <= now:
        table = await table_service.get_table_by_id(table_id, restaurant.id)
        return templates.TemplateResponse( "add_reservation.html",
                                           { "request": request,
                                             "table": table,
                                             "slug" : slug,
                                             "restaurant" : restaurant,
                                             "error": "Даты указаны некорректно. Бронирование должно быть в будущем и начинаться раньше окончания." },
                                             status_code=400 )
    await reservation_service.create_reservation(table_id, name, surname, phone, reservation_start, reservation_end, None, restaurant.id)
    return RedirectResponse(url=f"/r/{slug}/tables", status_code=303)

@router.get("/r/{slug}/tables/reservations/history")
async def reservations_page(request : Request, slug : str, reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    reservations = await reservation_service.get_all_reservations(restaurant.id)
    return templates.TemplateResponse("all_reservations.html", {"request" : request,
                                                                "reservations" : reservations,
                                                                "now": datetime.now(timezone.utc),
                                                                "slug" : slug,
                                                                "restaurant" : restaurant})

@router.post("/r/{slug}/tables/reservations/cancel/{reservation_id}")
async def cancel_reservation(request : Request, slug : str, reservation_id : int, reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant = await get_restaurant_dependency(slug)
    await reservation_service.cancel_reservation(reservation_id, restaurant.id)
    return RedirectResponse(url=f"/r/{slug}/tables/reservations/history", status_code=303)

@router.get("/r/{slug}/tables/reservations/history/search")
async def show_reservation(request : Request,
                           slug : str,
                           reservation_number : str | None = None,
                           name : str | None = None,
                           surname : str | None = None,
                           reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    reservation_uuid = None
    if reservation_number:
        reservation_uuid = UUID(reservation_number)
    reservations = await reservation_service.get_reservation_by_search(reservation_uuid, name, surname, restaurant.id)
    return templates.TemplateResponse("all_reservations.html", {"request": request,
                                                                "reservations": reservations,
                                                                "now": datetime.now(timezone.utc),
                                                                "slug" : slug,
                                                                "restaurant" : restaurant})
@router.get("/r/{slug}/tables/reservations/filtered_history")
async def filter_reservations(request : Request,
                              slug : str,
                              date : date | None = None,
                              status : str | None = None,
                              table_number : int | None = None,
                              reservation_service : ReservationService = Depends(get_reservation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    reservations = await reservation_service.filter_reservations(date, status, table_number, restaurant.id)
    return templates.TemplateResponse("all_reservations.html", {"request": request,
                                                                "reservations": reservations,
                                                                "now": datetime.now(timezone.utc),
                                                                "slug" : slug,
                                                                "restaurant" : restaurant})

@router.get("/r/{slug}/tables/get_free_table")
async def find_free_table(request : Request, slug : str):
    restaurant = await get_restaurant_dependency(slug)
    return templates.TemplateResponse("get_free_table.html", {"request" : request, "slug" : slug, "restaurant" : restaurant})

@router.post("/r/{slug}/tables/get_free_table")
async def find_free_table(response : Response,
                          slug : str,
                          people_amount : int = Form(..., lt=7),
                          requested_datetime : datetime = Form(),
                          service : TableService = Depends(get_table_service_dependency)):
    restaurant = await get_restaurant_dependency(slug)
    free_table = await service.get_free_table(people_amount, requested_datetime, restaurant.id)
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

@router.post("/r/{slug}/tables/confirm_reservation")
async def confirm_reservation(request : Request,
                              slug : str,
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
    restaurant = await get_restaurant_dependency(slug)
    table_id = data["table_id"]
    minutes = data["minutes"]
    reservation_end = None
    if minutes is None:
        reservation_end = requested_datetime + timedelta(hours=2)
    elif int(minutes) < 60:
        reservation_end = requested_datetime + timedelta(minutes=int(minutes))
    else:
        reservation_end = requested_datetime + timedelta(minutes=60)
    await service.create_reservation(table_id, name, surname, phone_number, requested_datetime, reservation_end, email, restaurant.id)
    return {"success": True, "message": "Бронирование успешно подтверждено."}

@router.get("/tables/available_tables")
async def get_available_tables(request : Request,
                               restaurant_id : UUID,
                               service : TableService = Depends(get_table_service_dependency),
                               internal_token : str = Header(..., alias="internal_token")):
    await verify_internal_token(internal_token)
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    available_tables = await service.find_all_available_tables(restaurant_id)
    return available_tables

