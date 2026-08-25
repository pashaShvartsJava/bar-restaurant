from fastapi import Request, APIRouter, HTTPException, Response
from fastapi.params import Depends
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from ..schemas.schema import LoginSchema, RegisterRequest, RegisterRequestDTO, AddressResponseDTO
from ..dependencies.dependency import get_service_dependency
from ..services.authentication_service import AuthenticationService, send_new_user_dto, send_address
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
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, max_age=3600, samesite="lax")
    return RedirectResponse(url="http://localhost:8005/users/my_profile/{identity_id}", status_code=303)

@router.post("/registration")
async def registration(data : RegisterRequest, service : AuthenticationService = Depends(get_service_dependency)):
    service.create_identity(data.email, data.password)
    created_user = service.find_by_email(data.email)
    user_request_dto : RegisterRequestDTO = send_new_user_dto(created_user.id, data.user_data.name,
                                                              data.user_data.surname, data.user_data.email,
                                                              data.user_data.birthday, data.user_data.phone,
                                                              created_user.role)
    address_request_dto : AddressResponseDTO = send_address(data.address_data.city, data.address_data.postal_code,
                                                                 data.address_data.street, data.address_data.house,
                                                                 data.address_data.apartment)
    register_dto = RegisterRequest(user_data=user_request_dto, address_data=address_request_dto)
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8005/users/add_user", json=register_dto.model_dump(mode="json"))
    return RedirectResponse(url="http//:localhost:8002/login", status_code=303)