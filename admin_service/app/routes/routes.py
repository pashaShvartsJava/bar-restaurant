import uuid
from datetime import date

import httpx
from asyncpg import InternalClientError
from fastapi import Request, APIRouter,Form
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from ..schema.admin import AdminUpdateDTO, AdminRegistrationDTO

from ..dependencies.dependencies import get_service_dependency
from ..security.role.role import IdentityRole
from ..service.admin_service import AdminService
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_role

from ..model.admin import AdminRole, Status

templates = Jinja2Templates(directory="app/templates_admin")
router = APIRouter()

@router.get("/admin_panel", response_class=HTMLResponse)
async def show_admin_panel(request: Request):
    payload = get_payload(request)
    required_role(IdentityRole.ADMIN, payload)
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
async def add_admin(request : Request, admin_service : AdminService = Depends(get_service_dependency),
              name: str = Form(),
              surname: str = Form(),
              birthday: date = Form(),
              phone: str = Form(),
              role : AdminRole = Form()
            ):
    payload = get_payload(request)
    required_role(IdentityRole.MODERATOR, payload)

    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.post("/admin_panel/delete_admin/{admin_id}")
async def delete_admin(request : Request, admin_id : int, admin_service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_role(IdentityRole.MODERATOR, payload)
    await admin_service.delete_admin(admin_id)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.get("/admin_panel/edit/{admin_id}")
async def show_edit_page(request : Request, admin_id : int, service : AdminService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_role(IdentityRole.ADMIN, payload)
    admin = await service.find_by_id(admin_id)
    return templates.TemplateResponse("edit_admin.html", {"request" : request, "admin" : admin})

@router.patch("/admin_panel/edit/{admin_id}")
async def edit_admin(request : Request, admin_id : int, service : AdminService = Depends(get_service_dependency),
               name : str = Form(),
               surname : str = Form(),
               birthday: date = Form(),
               role: AdminRole = Form()
               ):
    payload = get_payload(request)
    required_role(IdentityRole.ADMIN, payload)
    updated_admin = AdminUpdateDTO(name = name,
                                   surname = surname,
                                   birthday=birthday,
                                   role = role)
    await service.update_admin(admin_id, updated_admin)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.post("/admins/add_admin")
async def add_admin(request : Request, data : AdminRegistrationDTO, service : AdminService = Depends(get_service_dependency) ):
    try:
        await service.create_new_admin(data)
    except Exception:
        async with httpx.AsyncClient() as client:
            response = await client.patch("http://authentication-service:8000/edit_status", params={"status" : Status.FAILED.value, "str_email" : str(data.email)})
            response.raise_for_status()
        raise InternalClientError("Ошибка регистрации")

