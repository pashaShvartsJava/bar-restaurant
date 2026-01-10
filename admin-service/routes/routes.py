from datetime import datetime

from fastapi import Form

from ..main import *
from ..schema.admin import AdminRegistrationCreate
from ..repository.admin_repository import AdminRepository

@app.get("/admin/registration", response_class=HTMLResponse)
def registration(request: Request):
    return templates.TemplateResponse("registration.html", {"request" : request})

@app.post("/admin/registration", response_class=HTMLResponse)
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