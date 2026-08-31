from typing import Optional

import httpx
from fastapi import Request, APIRouter, Form
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from ..security.jwt.jwt import get_payload
from ..dependencies.dependency import get_service_dependency
from ..services.user_service import UserService
from ..schema.user_schema import RegisterRequest, IdentityRequest, PasswordResponse, PasswordDTO, EmailRequest
from datetime import date
from ..schema.user_schema import UserEditSchema

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

@router.get("/user/edit")
async def edit(request : Request, service : UserService = Depends(get_service_dependency)):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    return templates.TemplateResponse("user_edit.html", context={"request" : request, "user" : user, "address" : user.address})


@router.patch("/user/edit")
async def edit_user(request : Request, service : UserService = Depends(get_service_dependency),
                    name: Optional[str] = Form(None),
                    surname: Optional[str] = Form(None),
                    birthday: Optional[date] = Form(None),
                    phone: Optional[str] = Form(None),
                    email: Optional[str] = Form(None),
                    city: Optional[str] = Form(None),
                    street: Optional[str] = Form(None),
                    postal_code: Optional[int] = Form(None),
                    house: Optional[int] = Form(None),
                    apartment: Optional[int] = Form(None)):
    payload  = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    data = UserEditSchema(name=name, surname=surname,
                          birthday=birthday, phone=phone,
                          email=email, city=city, street=street, postal_code=postal_code,
                          house=house, apartment=apartment)
    if email is not None and email != user.email:
        request_email = EmailRequest(old_email=user.email, new_email=email)
        async with httpx.AsyncClient() as client:
            response = await client.patch(url="http://authentication-service:8000/edit_email", json=request_email.model_dump(mode="json"))
            response.raise_for_status()

    await service.update_user(user, data)

    return RedirectResponse(url="/user/my_profile", status_code=303)

@router.delete("/user/delete")
async def delete_user(request : Request, service : UserService = Depends(get_service_dependency)):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    await service.delete_user(user)
    async with httpx.AsyncClient() as client:
        response = await client.delete(url="http://authentication-service:8000/delete_identity", params={"identity_id" : user.identity_id})
        response.raise_for_status()
    return RedirectResponse(url="/bar_name", status_code=303)

@router.get("/user/password")
async def edit_password(request: Request,  service : UserService = Depends(get_service_dependency)):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    return templates.TemplateResponse("edit_password.html", context={"request" : request, "user" : user})

@router.patch("/user/password")
async def edit_password(request: Request,
                        service : UserService = Depends(get_service_dependency),
                        old_password : str = Form(),
                        new_password : str = Form(),
                        confirmed_password : str = Form()):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])

    if new_password != confirmed_password:
        return RedirectResponse(url="/user/password", status_code=303)

    async with httpx.AsyncClient() as client:
        response = await client.get(url="http://authentication-service:8000/get_identity", params={"identity_id" : user.identity_id,
                                                                                                   "old_password" : old_password})
        response.raise_for_status()
    user_password_response = PasswordResponse(**response.json())

    checked_passwords = await service.check_new_passwords(old_password, new_password, confirmed_password, user_password_response)

    if not checked_passwords:
        return RedirectResponse(url="/user/password", status_code=303)
    new_password_dto = PasswordDTO(identity_id=user.identity_id, new_password=new_password)
    async with httpx.AsyncClient() as client:
        response = await client.patch("http://authentication-service:8000/edit_password", json=new_password_dto.model_dump(mode="json"))
        response.raise_for_status()

    await logout()


