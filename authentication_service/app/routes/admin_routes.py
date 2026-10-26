import secrets
from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Form
from fastapi.params import Depends, Header
from pydantic import EmailStr, TypeAdapter
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from .owner_routes import logger
from ..exceptions.exceptions import InvalidCredentialsError
from ..model.identity_model import Status, IdentityRole
from ..schemas.admin_schema import AdminRegistration, AdminRegistrationDTO, AdminLogin
from ..schemas.restaurant_schema import KeyDTO, RestaurantStatus
from ..schemas.schema import LoginSchema
from ..dependencies.dependency import get_service_dependency, get_httpx_async_connection
from ..security.internal_security import verify_internal_token
from ..services.authentication_service import AuthenticationService
from ..security.rate_limit import check_login_rate_limit, reset_login_rate_limit
import httpx
from ..config.config import settings

templates = Jinja2Templates(directory="app/templates_auth")
router = APIRouter()
INTERNAL_TOKEN = settings.internal_token

@router.get("/admin/login", response_class=HTMLResponse)
def admin_login(request : Request):
    return templates.TemplateResponse("admin_login.html", {"request" : request})

@router.post("/admin/login")
async def admin_login(data : Annotated[AdminLogin, Form()],
                      client : Annotated[httpx.AsyncClient, Depends(get_httpx_async_connection)],
                      service : AuthenticationService = Depends(get_service_dependency)):
    credentials = LoginSchema(email=data.email, password=data.password)
    await check_login_rate_limit(str(data.email))
    identity = await service.find_by_email(data.email)
    response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_id",
                                headers={"internal_token": INTERNAL_TOKEN},
                                params={"identity_id" : str(identity.id)})
    if response.is_error:
        logger.warning("422 DETAIL: ", response.text)
    response.raise_for_status()
    restaurant_id = response.json()
    try:
        token = await service.admin_login(credentials, restaurant_id)
        await reset_login_rate_limit(str(data.email))
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail=[
        {
            "loc": ["body", "email"],
            "msg": "Неверный email или пароль"
        }
    ])
    key = await service.verify_authentication_key(data.authentication_key, data.email)
    key_dto = KeyDTO(restaurant_id=key.restaurant_id, identity_id=key.identity_id)
    async with httpx.AsyncClient() as client:
        response = await client.post("http://restaurant-service:8010/restaurants/get_restaurant_status",
                                    headers={"internal_token": INTERNAL_TOKEN},
                                    json=key_dto.model_dump(mode="json"))
        response.raise_for_status()
    restaurant_status = response.json()
    admin = await service.find_by_email(data.email)
    if not admin.verified_email:
        raise HTTPException(detail="У этого аккаунта не верифицирован email", status_code=403)
    if admin.status != Status.ACTIVE:
        raise HTTPException(detail="Этот аккаунт в состоянии незавершенной регистрации или заблокирован", status_code=403)
    if restaurant_status in (RestaurantStatus.CLOSED, RestaurantStatus.SUSPENDED, RestaurantStatus.PENDING):
        raise HTTPException(status_code=403, detail="Доступ запрещен. Подписка на данный аккаунт для управления платформой не оплачена или приостановлена.")
    redirect = RedirectResponse(url="/admin_panel", status_code=303)
    csrf_token = secrets.token_urlsafe(32)
    redirect.set_cookie(key="access_token", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    redirect.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=False, max_age=3600, samesite="lax")
    return redirect

@router.patch("/edit_status")
async def edit_status(status : Status, str_email : str, service : AuthenticationService = Depends(get_service_dependency)):
    email = TypeAdapter(EmailStr).validate_python(str_email)
    existing_identity = await service.find_by_email(email)
    await service.update_status_identity(existing_identity, status)

