from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Response, Form
from datetime import date
from fastapi.params import Depends
from jinja2.runtime import identity
from pydantic import EmailStr
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..exceptions.exceptions import InvalidCredentialsError, EmailError
from ..schemas.schema import LoginSchema, RegisterRequest, RegisterRequestDTO, AddressResponseDTO, PasswordUpdateDTO, \
    EmailRequest, RegistrationSchema
from ..dependencies.dependency import get_service_dependency
from ..security.password.password import verify_password
from ..services.authentication_service import AuthenticationService, send_new_user_dto, send_address
import httpx
from uuid import UUID

templates = Jinja2Templates(directory="app/templates_auth")
router = APIRouter()


@router.get("/bar_name", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse("main_page.html", context={"request": request})

@router.get("/login", response_class=HTMLResponse)
def authentication(request: Request):
    return templates.TemplateResponse("login.html", {"request" : request})

@router.get("/registration", response_class=HTMLResponse)
def registration(request: Request):
    return templates.TemplateResponse("registration.html", {"request" : request})

@router.post("/login", response_class=HTMLResponse)
async def authentication(email: EmailStr = Form(...),
                         password: str = Form(...),
                         service : AuthenticationService = Depends(get_service_dependency)):
    data = LoginSchema(email=email, password=password)
    try:
        token = await service.login(data)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail=[
        {
            "loc": ["body", "email"],
            "msg": "Неверный email или пароль"
        }
    ])

    redirect = RedirectResponse(url="/user/my_profile", status_code=303)
    redirect.set_cookie(key="access_token", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    return redirect

@router.post("/registration")
async def registration( data : Annotated[RegistrationSchema, Form()],
                        service: AuthenticationService = Depends(get_service_dependency)):
    await service.create_identity(data.email, data.password)
    try:
        created_user = await service.find_by_email(data.email)
    except EmailError:
        raise HTTPException(detail="Такой пользователь уже существует", status_code=409)
    user_request_dto : RegisterRequestDTO = send_new_user_dto(created_user.id,
                                                              data.name,
                                                              data.surname, data.email,
                                                              data.birthday, data.phone,
                                                              created_user.role)
    address_request_dto : AddressResponseDTO = send_address(data.city, data.postal_code,
                                                                 data.street, data.house,
                                                                 data.apartment)
    register_dto = RegisterRequest(user_data=user_request_dto, address_data=address_request_dto)
    async with httpx.AsyncClient() as client:
        response = await client.post("http://user-service:8005/users/add_user", json=register_dto.model_dump(mode="json"))
        response.raise_for_status()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/get_identity")
async def update_password(
    identity_id: UUID,
    old_password: str,
    new_password: str,
    service: AuthenticationService = Depends(get_service_dependency)
):
    identity = await service.find_by_identity(identity_id)

    checked_passwords = verify_password(
        old_password,
        identity.password_hash
    )

    if not checked_passwords:
        raise HTTPException(
            status_code=401,
            detail="Incorrect old password"
        )

    return await service.update_password(
        identity_id,
        new_password
    )

@router.patch("/edit_password")
async def update_password(data : PasswordUpdateDTO, service: AuthenticationService = Depends(get_service_dependency)):
    await service.update_password(data.identity_id, data.new_password)

@router.patch("/edit_email")
async def edit_email(data : EmailRequest, service: AuthenticationService = Depends(get_service_dependency)):
    identity = await service.find_by_email(data.old_email)
    already_existed_identity = await service.find_by_email(data.new_email)
    if already_existed_identity is not None:
        raise HTTPException(status_code=409, detail="Такой пользователь уже существует")
    await service.update_email(identity, data.new_email)

@router.delete("/delete_identity")
async def delete_identity(identity_id : UUID, service: AuthenticationService = Depends(get_service_dependency)):
    await service.delete_identity(identity_id)


