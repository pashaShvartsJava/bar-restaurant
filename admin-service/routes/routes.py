from ..main import *
from schema


@app.get("/admin/login", response_class=HTMLResponse)
def authentication(request: Request):
    return templates.TemplateResponse("login.html", {"request" : request})

@app.get("/admin/registration", response_class=HTMLResponse)
def registration(admin: AdminRegistrationCreate):

    return templates.TemplateResponse("registration.html", {"admin" : admin})