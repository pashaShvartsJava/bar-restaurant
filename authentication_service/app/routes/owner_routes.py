import secrets
from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Form
from fastapi.params import Depends, Header
from pydantic import EmailStr, TypeAdapter
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..schemas.admin_schema import AddAdminRequest, AdminRegistrationDTO
from ..exceptions.exceptions import InvalidCredentialsError
from ..model.identity_model import Status, IdentityRole
from ..schemas.admin_schema import IdentityEdit
from ..schemas.restaurant_schema import RestaurantRegistrationDTO, RestaurantCreationDTO
from ..schemas.schema import LoginSchema, RegisterRequest, RegisterRequestDTO, AddressResponseDTO, PasswordUpdateDTO, \
    EmailRequest, RegistrationSchema, IdentityDto
from ..dependencies.dependency import get_service_dependency, get_httpx_async_connection
from ..security.password.password import verify_password
from ..security.rate_limit import check_login_rate_limit, reset_login_rate_limit
from ..security.internal_security import verify_internal_token
from ..security.jwt.jwt import decode_access_token
from ..services.authentication_service import AuthenticationService, send_new_user_dto, send_address
import httpx
from uuid import UUID
from ..config.config import settings

INTERNAL_TOKEN = settings.internal_token
templates = Jinja2Templates(directory="app/templates_auth")
router = APIRouter()

@router.get("/restaurant-platform")
async def get_main_owner_page(request : Request):
    return templates.TemplateResponse("main_page_for_restaurant_owners.html", {"request" : request})

@router.get("/restaurant/register")
async def create_restaurant(request : Request):
    return templates.TemplateResponse("owner_registration.html", {"request" : request})

@router.post("/restaurant/register")
async def create_restaurant(data : Annotated[RestaurantRegistrationDTO, Form()],
                            client : Annotated[httpx.AsyncClient, Depends(get_httpx_async_connection)],
                            service : AuthenticationService = Depends(get_service_dependency)):
    existing_owner = await service.find_by_email(data.email)
    if existing_owner is not None and (
            existing_owner.status == Status.ACTIVE or existing_owner.status == Status.BLOCKED):
        raise HTTPException(detail="Такой пользователь уже существует", status_code=409)
    r_dto = RestaurantCreationDTO(
        country=data.country,
        city=data.city,
        address=data.address,
        restaurant_name=data.restaurant_name
    )
    r_response = await client.post("http://restaurant-service/restaurants/add_restaurant",
                                 headers={"internal_token" : INTERNAL_TOKEN},
                                 json=r_dto.model_dump(mode="json"))
    r_response.raise_for_status()
    restaurant_id = r_response.json()
    if existing_owner is not None and (existing_owner.status==Status.PENDING or existing_owner.status==Status.FAILED):
        old_admin_dto = AdminRegistrationDTO(identity_id=existing_owner.id, name=data.name,
                                             surname=data.surname, phone=data.phone,
                                             birthday=data.birthday, email=existing_owner.email)
        response = await client.post("http://admin-service:8002/admins/add_admin",
                                     json=old_admin_dto.model_dump(mode="json"),
                                     headers={"internal_token": INTERNAL_TOKEN},
                                     params={"restaurant_id" : restaurant_id})
        response.raise_for_status()
        await service.create_owner_key(restaurant_id)
        await service.update_status_identity(existing_owner, Status.ACTIVE)
        return RedirectResponse(url="/choose_subscription", status_code=303)

    created_owner = await service.create_admin_identity(data.email, data.password)
    created_owner_dto = AdminRegistrationDTO(identity_id=created_owner.id, name=data.name,
                                         surname=data.surname, phone=data.phone,
                                         birthday=data.birthday, email=created_owner.email)
    a_response = await client.post("http://admin-service:8002/admins/add_admin",
                                     json=created_owner_dto.model_dump(mode="json"),
                                     headers={"internal_token": INTERNAL_TOKEN},
                                     params={"restaurant_id" : restaurant_id})
    a_response.raise_for_status()
    await service.create_owner_key(restaurant_id)
    await service.update_status_identity(created_owner.id, Status.ACTIVE)
    return RedirectResponse(url="/choose_subscription", status_code=303)

@router.get("/choose_subscription")
async def choose_subscription(request : Request):
    return templates.TemplateResponse("choose_subscription.html", {"request" : request})

