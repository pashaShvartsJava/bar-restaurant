import uuid
from datetime import date

import httpx
from asyncpg import InternalClientError
from fastapi import Request, APIRouter, Form, HTTPException
from fastapi.params import Depends
from jinja2.runtime import identity
from pydantic import EmailStr
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.templating import Jinja2Templates
from ..schema.admin import AdminUpdateDTO, AdminRegistrationDTO, IdentityEdit, AdminRegistrationForm, AddAdminRequest
from typing import Annotated

from ..dependencies.dependencies import get_service_dependency
from ..security.role.role import IdentityRole
from ..service.admin_service import AdminService
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_role, required_roles

from ..model.admin import Status

templates = Jinja2Templates(directory="app/templates_admin")
router = APIRouter()

@router.post("/admin/logout")
def logout():
    redirect = RedirectResponse(url="/admin/login", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect

@router.get("/admin_panel", response_class=HTMLResponse)
async def show_admin_panel(request: Request):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    return templates.TemplateResponse("admin_panel.html", {"request" : request})

@router.get("/admin_panel/all_admins")
async def show_all_admins(request: Request, admin_service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_role(IdentityRole.MODERATOR, payload)
    admins = await admin_service.find_all_admins()
    return templates.TemplateResponse('all_admins.html', {"request" : request, "admins" : admins})

@router.get("/admin_panel/all_admins/add_admin")
def show_page_add_admin(request : Request):
    payload = get_payload(request)
    required_role(IdentityRole.MODERATOR, payload)
    return templates.TemplateResponse("add_admins.html", {"request" : request})

@router.post("/admin_panel/all_admins/add_admin")
async def add_admin(request : Request, data : Annotated[AdminRegistrationForm, Form()],
                    admin_service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_role(IdentityRole.MODERATOR, payload)
    identity_id = uuid.uuid4()
    new_identity = AddAdminRequest(identity_id=identity_id, email=data.email, password=data.password, role=data.role, status=Status.ACTIVE)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url="http://authentication-service:8000/add_identity", json=new_identity.model_dump(mode="json"))
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 409:
                raise HTTPException(status_code=409, detail=[{"loc": ["body", "email"], "msg": "Этот email уже занят"}])
    try:
        await admin_service.add_new_admin(data, identity_id)
    except:
        raise HTTPException(detail="Ошибка сервера. Не удалось создать администратора", status_code=500)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.post("/admin_panel/delete_admin/{admin_id}")
async def delete_admin(request : Request, admin_id : int, admin_service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_role(IdentityRole.MODERATOR, payload)
    admin = await admin_service.find_by_id(admin_id)
    async with httpx.AsyncClient() as client:
        response = await client.delete(url="http://authentication-service:8000/delete_identity", params={"identity_id" : admin.identity_id})
        response.raise_for_status()
    if response.status_code >= 400:
        detail = response.json().get("detail", "Ошибка удаления")
        raise HTTPException(status_code=response.status_code,detail=detail)
    try:
        await admin_service.delete_admin(admin_id)
    except HTTPException:
        raise HTTPException(status_code=500, detail="Ошибка удаления данных")
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.get("/admin_panel/edit/{admin_id}")
async def show_edit_page(request : Request, admin_id : int, service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    admin = await service.find_by_id(admin_id)
    return templates.TemplateResponse("edit_admin.html", {"request" : request, "admin" : admin})

@router.patch("/admin_panel/edit/{admin_id}")
async def edit_admin(request : Request, admin_id : int, service : AdminService = Depends(get_service_dependency),
               name : str | None = Form(None),
               surname : str | None  = Form(None),
               phone : str | None = Form(None),
               birthday: date | None  = Form(None),
               email: EmailStr | None = Form(None),
               role: IdentityRole | None  = Form(None)
               ):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    updated_admin = AdminUpdateDTO(name = name,
                                   surname = surname,
                                   phone=phone,
                                   birthday=birthday,
                                   email=email,
                                   role = role)
    admin = await service.find_by_id(admin_id)
    data = IdentityEdit(identity_id=admin.identity_id, role=role, email=email)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch("http://authentication-service:8000/edit_identity",json=data.model_dump(mode="json"))
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 409:
                raise HTTPException(status_code=409, detail=[{"loc": ["body", "email"], "msg": "Этот логин уже занят"}])

    try:
        await service.update_admin(admin_id, updated_admin)
    except HTTPException:
        raise HTTPException(detail="Ошибка сохранения данных", status_code=500)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.post("/admins/add_admin")
async def add_admin(data : AdminRegistrationDTO, service : AdminService = Depends(get_service_dependency)):
    try:
        await service.create_new_admin(data)
    except Exception:
        async with httpx.AsyncClient() as client:
            response = await client.patch("http://authentication-service:8000/edit_status", params={"status" : Status.FAILED.value, "str_email" : str(data.email)})
            response.raise_for_status()
        raise InternalClientError("Ошибка регистрации")

@router.get("/admin_panel/edit/password/{id}")
async def edit_password_page(request : Request, id : int, service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    admin = await service.find_by_identity(payload["sub"])
    if admin.id != id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return templates.TemplateResponse("edit_password.html", {"request" : request, "admin" : admin})

@router.patch("/admin_panel/edit/password/{id}")
async def edit_password(request: Request, service: AdminService = Depends(get_service_dependency),
                        old_password: str = Form(..., min_length=8, description="password"),
                        new_password: str = Form(..., min_length=8, description="password"),
                        confirmed_password: str = Form(..., min_length=8, description="password")):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    admin = await service.find_by_identity(payload["sub"])

    if new_password != confirmed_password:
        raise HTTPException(status_code=400,detail="Пароли не совпадают")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url="http://authentication-service:8000/get_identity",
                params={"identity_id": admin.identity_id,"old_password": old_password,"new_password": new_password})
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401,detail="Неверный старый пароль")
        raise HTTPException(status_code=500,detail="Ошибка при смене пароля")
    response = JSONResponse({"success": True})
    response.delete_cookie("access_token")
    return response

