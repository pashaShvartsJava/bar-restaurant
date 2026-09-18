import uuid
from datetime import date

import httpx
from asyncpg import InternalClientError
from fastapi import Request, APIRouter, Form, HTTPException
from fastapi.params import Depends
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
from uuid import UUID

from ..model.admin import Status
from ..config.config import settings


INTERNAL_TOKEN = settings.internal_token
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
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://support-service:8006/support/unread/count"
        )

    support_data = response.json()
    unread_support_count = support_data["count"]
    return templates.TemplateResponse("admin_panel.html", {"request" : request, "unread_support_count" : unread_support_count})

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

@router.get("/admin_panel/all_customers")
async def show_all_customers(request : Request):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://user-service:8005/get_all_users", headers={"internal_token" : INTERNAL_TOKEN} )
        response.raise_for_status()
    users = response.json()

    async with httpx.AsyncClient() as client:
        response2 = await client.get(url="http://authentication-service:8000/get_all_identities", headers={"internal_token" : INTERNAL_TOKEN} )
        response2.raise_for_status()
    identities = response2.json()

    statuses_by_id = {identity["id"]: identity["status"] for identity in identities}
    for user in users:
        user["status"] = statuses_by_id.get(str(user["identity_id"]))

    return templates.TemplateResponse("all_users.html", {"request" : request, "users" : users})

@router.patch("/admin_panel/all_customers/{identity_id}/block")
async def block_customer(identity_id: UUID):
    async with httpx.AsyncClient() as client:
        response = await client.patch("http://authentication-service:8000/edit_status",
                                      params={"identity_id" : str(identity_id), "status" : Status.BLOCKED.value},
                                      headers={"internal_token" : INTERNAL_TOKEN})
        response.raise_for_status()

@router.patch("/admin_panel/all_customers/{identity_id}/unblock")
async def unblock_customer(identity_id: UUID):
    async with httpx.AsyncClient() as client:
        response = await client.patch("http://authentication-service:8000/edit_status",
                                      params={"identity_id" : str(identity_id), "status" : Status.ACTIVE.value},
                                      headers={"internal_token" : INTERNAL_TOKEN})
        response.raise_for_status()

@router.get("/admin_panel/all_customers/found_customer")
async def search_customer(request : Request, client_id : UUID):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://user-service:8005/get_all_users",
                                    headers={"internal_token": INTERNAL_TOKEN})
        response.raise_for_status()
    users = response.json()

    async with httpx.AsyncClient() as client:
        response2 = await client.get(url="http://authentication-service:8000/get_all_identities",
                                     headers={"internal_token": INTERNAL_TOKEN})
        response2.raise_for_status()
    identities = response2.json()

    statuses_by_id = {identity["id"]: identity["status"] for identity in identities}
    for user in users:
        user["status"] = statuses_by_id.get(str(user["identity_id"]))
    client = []
    for user in users:
        if user["identity_id"] == str(client_id):
            client.append(user)
    return templates.TemplateResponse("all_users.html", {"request" : request, "users" : client})

@router.get("/admin_panel/all_customers/{identity_id}")
async def customer_info(request : Request, identity_id : UUID):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://user-service:8005/get_user_address",
                                    params={"identity_id" : str(identity_id)},
                                    cookies={"access_token": request.cookies.get("access_token")})
        response.raise_for_status()
    info_user = response.json()

    async with httpx.AsyncClient() as client:
        response2 = await client.get("http://authentication-service:8000/get_status",
                                     params={"identity_id": str(identity_id)},
                                     headers={"internal_token": INTERNAL_TOKEN})
        identity = response2.json()
        info_user["status"] = identity["status"]
        info_user["identity_id"] = str(identity_id)
    return templates.TemplateResponse("user_info.html", {"request" : request, "user" : info_user})


