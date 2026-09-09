from typing import Annotated

from fastapi import Request, APIRouter, HTTPException, Form
from fastapi.params import Depends, Header
from pydantic import EmailStr
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..schemas.admin_schema import AddAdminRequest
from ..exceptions.exceptions import InvalidCredentialsError
from ..model.identity_model import Status, IdentityRole
from ..schemas.admin_schema import IdentityEdit
from ..schemas.schema import LoginSchema, RegisterRequest, RegisterRequestDTO, AddressResponseDTO, PasswordUpdateDTO, \
    EmailRequest, RegistrationSchema, IdentityDto
from ..dependencies.dependency import get_service_dependency
from ..security.password.password import verify_password
from ..services.authentication_service import AuthenticationService, send_new_user_dto, send_address
import httpx
from uuid import UUID
from ..config.config import settings

INTERNAL_TOKEN = settings.internal_token
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
    user = await service.find_by_email(email)
    if user.status != Status.ACTIVE:
        raise HTTPException(detail="Этот аккаунт в состоянии незавершенной регистрации или заблокирован",
                            status_code=403)

    redirect = RedirectResponse(url="/user/my_profile", status_code=303)
    redirect.set_cookie(key="access_token", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    return redirect

@router.post("/registration")
async def registration( data : Annotated[RegistrationSchema, Form()],
                        service: AuthenticationService = Depends(get_service_dependency)):
    existing_user = await service.find_by_email(data.email)
    if existing_user is not None and (existing_user.status==Status.ACTIVE or existing_user.status==Status.BLOCKED):
        raise HTTPException(detail="Такой пользователь уже существует", status_code=409)
    if existing_user is not None and (existing_user.status == Status.PENDING or existing_user.status == Status.FAILED):
        old_user_request_dto: RegisterRequestDTO = send_new_user_dto(existing_user.id,
                                                                 data.name,
                                                                 data.surname, data.email,
                                                                 data.birthday, data.phone,
                                                                 existing_user.role)
        old_address_request_dto: AddressResponseDTO = send_address(data.city, data.postal_code,
                                                               data.street, data.house,
                                                               data.apartment)

        old_register_dto = RegisterRequest(user_data=old_user_request_dto, address_data=old_address_request_dto)
        async with httpx.AsyncClient() as client:
            response = await client.post("http://user-service:8005/users/add_user",
                                         json=old_register_dto.model_dump(mode="json"))
            response.raise_for_status()
        return RedirectResponse(url="/login", status_code=303)

    created_user = await service.create_identity(data.email, data.password)
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
async def update_password(identity_id: UUID, old_password: str, new_password: str,
    service: AuthenticationService = Depends(get_service_dependency)):
    identity = await service.find_by_identity(identity_id)

    checked_passwords = verify_password(
        old_password,
        identity.password_hash
    )

    if not checked_passwords:
        raise HTTPException(status_code=401, detail="Incorrect old password")
    return await service.update_password(identity_id, new_password)

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
    try:
        await service.delete_identity(identity_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Ошибка удаления")

@router.patch("/edit_identity")
async def edit_identity(data : IdentityEdit, service: AuthenticationService = Depends(get_service_dependency)):
    taken_identity = await service.find_by_email(data.email)
    if taken_identity is not None and taken_identity.id != data.identity_id:
        raise HTTPException(detail="Этот email уже занят", status_code=409)
    identity = await service.find_by_identity(data.identity_id)
    await service.update_identity(identity, data)

@router.post("/add_identity")
async def add_new_identity(data : AddAdminRequest, service: AuthenticationService = Depends(get_service_dependency)):
    taken_identity = await service.find_by_email(data.email)
    if taken_identity is not None and taken_identity.id != data.identity_id:
        raise HTTPException(detail="Этот email уже занят", status_code=409)
    await service.add_new_identity(data)

@router.get("/get_all_identities")
async def get_all_identities(service: AuthenticationService = Depends(get_service_dependency),
                       internal_token : str = Header(..., alias="internal_token")):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    identities = await service.get_all_identities()
    return [IdentityDto.model_validate(identity).model_dump(mode="json") for identity in identities]

@router.patch("/edit_status")
async def edit_status(identity_id : UUID, status : Status,
                      internal_token : str = Header(..., alias="internal_token"),
                      service: AuthenticationService = Depends(get_service_dependency)):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    identity = await service.find_by_identity(identity_id)
    await service.update_status_identity(identity, status)

@router.get("/get_status")
async def get_status(identity_id : UUID, internal_token : str = Header(..., alias="internal_token"),
                     service: AuthenticationService = Depends(get_service_dependency)):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await service.find_by_identity(identity_id)
    return IdentityDto.model_validate(user).model_dump(mode="json")






