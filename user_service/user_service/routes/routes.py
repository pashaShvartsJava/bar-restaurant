from fastapi import Request, Response, APIRouter
import httpx
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from security.jwt import get_payload
from ..dependencies.dependency import get_service_dependency
from ..services.user_service import UserService
from ..schema.user_schema import RegisterRequest

templates = Jinja2Templates(directory="user_service/templates")
router = APIRouter()

@router.get("/user/my_profile")
def get_user_profile(request : Request, service : UserService = Depends(get_service_dependency)):
    payload = get_payload(request)
    user = service.find_by_identity_id(payload["sub"])
    return templates.TemplateResponse("user_profile.html", context={"request": request, "user": user, "address": user.address})

@router.post("http://localhost:8005/users/add_user")
def register_user(data : RegisterRequest, service : UserService = Depends(get_user_profile)):
    service.create_user(data.user_data, data.address_data)
    return RedirectResponse(url="http://localhost:8000/login", status_code=303)