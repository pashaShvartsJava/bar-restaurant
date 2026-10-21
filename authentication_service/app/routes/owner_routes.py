import secrets
import uuid
from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Form
from fastapi.params import Depends, Header
from jinja2.runtime import identity
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
from ..schemas.subscription_schema import SubscriptionCheckoutDTO, SubscriptionDTO, PLANS
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

async def create_restaurant_dto(data : Annotated[RestaurantRegistrationDTO, Form()], identity_id : UUID):
    r_dto = RestaurantCreationDTO(
        country=data.country,
        city=data.city,
        address=data.address,
        restaurant_name=data.restaurant_name,
        slug=data.slug,
        timezone=data.timezone,
        restaurant_currency=data.restaurant_currency,
        identity_id=identity_id
    )
    async with httpx.AsyncClient() as client:
        r_response = await client.post("http://restaurant-service:8010/restaurants/add_restaurant",
                                       headers={"internal_token": INTERNAL_TOKEN},
                                       json=r_dto.model_dump(mode="json"))
        r_response.raise_for_status()
        restaurant_id = r_response.json()
    return restaurant_id

@router.get("/restaurant-platform")
async def get_main_owner_page(request : Request):
    return templates.TemplateResponse("main_page_for_restaurant_owners.html", {"request" : request})

@router.get("/restaurant/register")
async def create_restaurant(request : Request):
    return templates.TemplateResponse("owner_registration.html", {"request" : request})

@router.post("/restaurant/register")
async def create_restaurant_and_subscription_checkout(data : Annotated[RestaurantRegistrationDTO, Form()],
                                                      client : Annotated[httpx.AsyncClient, Depends(get_httpx_async_connection)],
                                                      service : AuthenticationService = Depends(get_service_dependency)):
    existing_owner = await service.find_by_email(data.email)
    if existing_owner is not None and (
            existing_owner.status == Status.ACTIVE or existing_owner.status == Status.BLOCKED):
        raise HTTPException(detail="Такой пользователь уже существует", status_code=409)

    if existing_owner is not None and (existing_owner.status==Status.PENDING or existing_owner.status==Status.FAILED):
        restaurant_id = await create_restaurant_dto(data, existing_owner.id)
        old_admin_dto = AdminRegistrationDTO(identity_id=existing_owner.id, name=data.name,
                                             surname=data.surname, phone=data.phone,
                                             birthday=data.birthday, email=existing_owner.email, role=IdentityRole.OWNER)
        response = await client.post("http://admin-service:8002/admins/add_admin",
                                     json=old_admin_dto.model_dump(mode="json"),
                                     headers={"internal_token": INTERNAL_TOKEN},
                                     params={"restaurant_id" : restaurant_id})
        if response.is_error:
            print("Admin service status:", response.status_code)
            print("Admin service response:", response.text)
        response.raise_for_status()
        await service.update_status_identity(existing_owner, Status.ACTIVE)
        return RedirectResponse(url="/choose_subscription", status_code=303)
    identity_id = uuid.uuid4()
    restaurant_id = await create_restaurant_dto(data, identity_id)
    created_owner = await service.create_admin_identity(data.email, data.password, IdentityRole.OWNER, restaurant_id, identity_id)
    created_owner_dto = AdminRegistrationDTO(identity_id=created_owner.id, name=data.name,
                                         surname=data.surname, phone=data.phone,
                                         birthday=data.birthday, email=created_owner.email, role=IdentityRole.OWNER)
    a_response = await client.post("http://admin-service:8002/admins/add_admin",
                                     json=created_owner_dto.model_dump(mode="json"),
                                     headers={"internal_token": INTERNAL_TOKEN},
                                     params={"restaurant_id" : restaurant_id})
    if a_response.is_error:
        print("Admin service status:", a_response.status_code)
        print("Admin service response:", a_response.text)
    a_response.raise_for_status()
    await service.update_status_identity(created_owner, Status.ACTIVE)
    plan = PLANS.get(data.plan_id)
    if plan is None:
        raise HTTPException(detail="Invalid plan", status_code=400)
    server_trial = plan["trial_days"]
    server_currency = plan["currency"]
    server_price = plan[data.billing_period]
    if server_price != data.price:
        raise HTTPException(detail="Invalid price entered", status_code=400)
    if server_trial != data.trial_days:
        raise HTTPException(detail="Invalid trial day period entered", status_code=400)
    if server_currency != data.currency:
        raise HTTPException(detail="Invalid currency entered", status_code=400)

    subscription_checkout_dto = SubscriptionCheckoutDTO(
        user_id=created_owner.id,
        email=created_owner.email,
        plan_id=data.plan_id,
        billing_period=data.billing_period.value,
        trial_days=server_trial,
        price=server_price,
        currency=server_currency.value
    )
    checkout_response = await client.post("http://payment-service:8008/payment/subscription",
                                          headers={"internal-token" : INTERNAL_TOKEN},
                                          json=subscription_checkout_dto.model_dump(mode="json"))
    checkout_response.raise_for_status()
    return checkout_response.json()

@router.get("/choose_subscription")
async def choose_subscription(request : Request):
    return templates.TemplateResponse("choose_subscription.html", {"request" : request})

