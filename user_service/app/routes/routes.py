from fastapi import Request, APIRouter
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from ..security.jwt.jwt import get_payload
from ..dependencies.dependency import get_service_dependency
from ..services.user_service import UserService
from ..schema.user_schema import RegisterRequest

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/user/my_profile")
async def get_user_profile(request : Request, service : UserService = Depends(get_service_dependency)):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    return templates.TemplateResponse("user_profile.html", context={"request": request, "user": user, "address": user.address})

@router.post("/users/add_user")
async def register_user(data : RegisterRequest, service : UserService = Depends(get_service_dependency)):
    await service.create_user(data.user_data, data.address_data)
    return {"message": "User created successfully"}

@router.post("/logout")
async def logout():
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect
