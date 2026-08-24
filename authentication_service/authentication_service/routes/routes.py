from fastapi import Request, APIRouter, HTTPException, Response
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from ..schemas.schema import LoginSchema, RegistrationSchema, RegisterRequestDTO
from ..dependencies.dependency import get_service_dependency
from ..services.authentication_service import AuthenticationService, send_new_user_dto
import httpx

templates = Jinja2Templates(directory="authentication_service/templates_auth")
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
def authentication(response : Response,
                   data : LoginSchema,
                   service : AuthenticationService = Depends(get_service_dependency)):
    try:
        token = service.login(data)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication failed: invalid login or password")
    response.set_cookie(key="jwt", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    return RedirectResponse(url="http://localhost:8005/users/my_profile/{identity_id}", status_code=303)

@router.post("/registration")
async def registration(data : RegistrationSchema, service : AuthenticationService = Depends(get_service_dependency)):
    service.create_identity(data.email, data.password)
    user_request_dto : RegisterRequestDTO = send_new_user_dto(data.name, data.surname,data.birthday, data.phone, data.role)
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8005/users/add_user", json=user_request_dto.model_dump(mode="json"))
    return RedirectResponse(url="http//:localhost:8002/login", status_code=303)