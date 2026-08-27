from fastapi import Request, APIRouter, HTTPException, Response, Form
from datetime import date
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from ..schemas.schema import LoginSchema, RegisterRequest, RegisterRequestDTO, AddressResponseDTO
from ..dependencies.dependency import get_service_dependency
from ..services.authentication_service import AuthenticationService, send_new_user_dto, send_address
import httpx

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
async def authentication(email: str = Form(...),
                         password: str = Form(...),
                         service : AuthenticationService = Depends(get_service_dependency)):
    data = LoginSchema(email=email, password=password)
    try:
        token = await service.login(data)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication failed: invalid login or password")

    redirect = RedirectResponse(url="/user/my_profile", status_code=303)
    redirect.set_cookie(key="access_token", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    print("REDIRECT LOCATION:", redirect.headers.get("location"))
    print("SET COOKIE:", redirect.headers.get("set-cookie"))
    return redirect

@router.post("/registration")
async def registration( name: str = Form(...),
                        surname: str = Form(...),
                        phone: str = Form(...),
                        birthday: date = Form(...),
                        city: str = Form(...),
                        postal_code: int = Form(...),
                        street: str = Form(...),
                        house: int = Form(...),
                        apartment: int = Form(...),
                        email: str = Form(...),
                        password: str = Form(...),
                        service: AuthenticationService = Depends(get_service_dependency)):
    await service.create_identity(email, password)
    try:
        created_user = await service.find_by_email(email)
    except HTTPException:
        raise HTTPException(detail="Such user already exists", status_code=401)
    user_request_dto : RegisterRequestDTO = send_new_user_dto(created_user.id,
                                                              name,
                                                              surname, email,
                                                              birthday, phone,
                                                              created_user.role)
    address_request_dto : AddressResponseDTO = send_address(city, postal_code,
                                                                 street, house,
                                                                 apartment)
    register_dto = RegisterRequest(user_data=user_request_dto, address_data=address_request_dto)
    async with httpx.AsyncClient() as client:
        response = await client.post("http://user-service:8005/users/add_user", json=register_dto.model_dump(mode="json"))
        print("USER _SERVICE STATUS CODE: ", response.status_code)
        print("USER _SERVICE STATUS TEXT: ", response.text)
        response.raise_for_status()
    return RedirectResponse(url="/login", status_code=303)