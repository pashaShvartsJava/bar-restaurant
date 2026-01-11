from datetime import datetime
from fastapi import Request, APIRouter,Form
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from admin_service.repository.admin_repository import AdminRepository
from admin_service.schema.admin import AdminRegistrationCreate


templates = Jinja2Templates(directory="templates_admin")
router = APIRouter()

@router.get("/admin/registration", response_class=HTMLResponse)
def registration(request: Request):
    return templates.TemplateResponse("registration.html", {"request" : request})

@router.post("/admin/registration", response_class=HTMLResponse)
def registration(request: Request,
                 name: str = Form(...),
                 surname: str = Form(...),
                 phone: str = Form(...),
                 email: str = Form(...),
                 birthday: datetime = Form(...),
                 password: str = Form(...)
                 ):
    admin = AdminRegistrationCreate(name = name,
                                    surname = surname,
                                    phone = phone,
                                    email = email,
                                    birthday = birthday,
                                    password = password
                                    )
    AdminRepository.create_admin(admin)
    return templates.TemplateResponse("login.html", {"request" : request})