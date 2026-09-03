from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Form
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..exceptions.exceptions import InvalidCredentialsError
from ..schemas.admin_schema import AdminRegistration, AdminRegistrationDTO, AdminLogin
from ..schemas.schema import LoginSchema
from ..dependencies.dependency import get_service_dependency
from ..services.authentication_service import AuthenticationService, send_new_user_dto, send_address
import httpx

templates = Jinja2Templates(directory="app/templates_auth")
router = APIRouter()

@router.get("/admin/login", response_class=HTMLResponse)
def admin_login(request : Request):
    return templates.TemplateResponse("admin_login.html", {"request" : request})

@router.get("/admin/registration", response_class=HTMLResponse)
def admin_registration(request : Request):
    return templates.TemplateResponse("admin_registration.html", {"request" : request})

@router.post("/admin/registration")
async def admin_registration(data : Annotated[AdminRegistration, Form()], service : AuthenticationService = Depends(get_service_dependency)):
    existing_admin = await service.find_by_email(data.email)
    if existing_admin is not None:
        raise HTTPException(detail="Такой пользователь уже существует", status_code=409)
    key = await service.verify_registration_key(data.registration_key)
    if key is None:
        raise HTTPException(detail="Доступ запрещен", status_code=403)

    created_admin = await service.create_admin_identity(data.email, data.password)
    admin_dto = AdminRegistrationDTO(identity_id=created_admin.id, name=data.name, surname=data.surname, phone=data.phone, birthday=data.birthday, email=data.email)

    async with httpx.AsyncClient() as client:
        response = await client.post("http://admin-service:8002/admins/add_admin",
                                     json=admin_dto.model_dump(mode="json"))
        response.raise_for_status()
    return RedirectResponse(url="/admin/login", status_code=303)

@router.post("/admin/login")
async def admin_login(data : Annotated[AdminLogin, Form()], service : AuthenticationService = Depends(get_service_dependency) ):
    credentials = LoginSchema(email=data.email, password=data.password)
    try:
        token = await service.login(credentials)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail=[
        {
            "loc": ["body", "email"],
            "msg": "Неверный email или пароль"
        }
    ])
    authentication_key = await service.verify_authentication_key(data.authentication_key)
    if authentication_key is None:
        raise HTTPException(detail="Доступ запрещен", status_code=403)
    redirect = RedirectResponse(url="/admin_panel", status_code=303)
    redirect.set_cookie(key="access_token", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    return redirect

