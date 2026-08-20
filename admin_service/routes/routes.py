from datetime import date
from fastapi import Request, APIRouter,Form
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from admin_service.schema.admin import AdminRegistrationDTO, AdminUpdateDTO

from admin_service.dependencies.dependencies import get_service_dependency
from admin_service.service.admin_service import AdminService

from admin_service.model.admin import AdminRole

templates = Jinja2Templates(directory="admin_service/templates_admin")
router = APIRouter()

@router.get("/admin_panel", response_class=HTMLResponse)
def show_admin_panel(request: Request):
    return templates.TemplateResponse("admin_panel.html", {"request" : request})

@router.get("/admin_panel/all_admins")
def show_all_admins(request: Request, admin_service : AdminService = Depends(get_service_dependency)):
    admins = admin_service.find_all_admins()
    return templates.TemplateResponse('all_admins.html', {"request" : request, "admins" : admins})

@router.get("/admin_panel/all_admins/add_admin")
def show_page_add_admin(request : Request):
    return templates.TemplateResponse("add_admins.html", {"request" : request})

@router.post("/admin_panel/all_admins/add_admin")
def add_admin(admin_service : AdminService = Depends(get_service_dependency),
              name: str = Form(),
              surname: str = Form(),
              birthday: date = Form(),
              phone: str = Form(),
              email : str = Form(),
              password : str = Form(),
              role : AdminRole = Form()
            ):
    new_admin = AdminRegistrationDTO(
        name=name, surname=surname, birthday=birthday, phone=phone, email=email, password=password, role = role
    )
    admin_service.create_new_admin(new_admin)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.post("/admin_panel/delete_admin/{admin_id}")
def delete_admin(admin_id : int, admin_service : AdminService = Depends(get_service_dependency)):
    admin_service.delete_admin(admin_id)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)

@router.get("/admin_panel/edit/{admin_id}")
def show_edit_page(request : Request, admin_id : int, service : AdminService = Depends(get_service_dependency)):
    admin = service.find_by_id(admin_id)
    return templates.TemplateResponse("edit_admin.html", {"request" : request, "admin" : admin})

@router.patch("/admin_panel/edit/{admin_id}")
def edit_admin(admin_id : int, service : AdminService = Depends(get_service_dependency),
               name : str = Form(),
               surname : str = Form(),
               birthday: date = Form(),
               phone: str = Form(),
               email: str = Form(),
               role: AdminRole = Form()
               ):
    updated_admin = AdminUpdateDTO(name = name,
                                   surname = surname,
                                   birthday=birthday,
                                   phone=phone,
                                   email=email,
                                   role = role)
    service.update_admin(admin_id, updated_admin)
    return RedirectResponse(url="/admin_panel/all_admins", status_code=303)


