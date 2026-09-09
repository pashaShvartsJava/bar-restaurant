from http.client import HTTPException
from typing import Annotated

import httpx
from asyncpg import InternalClientError
from fastapi import Request, APIRouter, Form, HTTPException
from fastapi.params import Depends, Header
from starlette.responses import RedirectResponse, JSONResponse
from starlette.templating import Jinja2Templates

from ..model.user_model import Status
from ..security.jwt.jwt import get_payload
from ..dependencies.dependency import get_service_dependency
from ..services.user_service import UserService
from ..schema.user_schema import RegisterRequest, EmailRequest, UserDto, UserInfo
from ..schema.user_schema import UserEditSchema
from ..config.config import settings
from uuid import UUID

INTERNAL_TOKEN = settings.internal_token
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/user/my_profile")
async def get_user_profile(request : Request, service : UserService = Depends(get_service_dependency)):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    return templates.TemplateResponse("user_profile.html", context={"request": request, "user": user, "address": user.address})

@router.post("/users/add_user")
async def register_user(data : RegisterRequest, service : UserService = Depends(get_service_dependency)):
    try:
        await service.create_user(data.user_data, data.address_data)
    except Exception:
        async with httpx.AsyncClient() as client:
            response = await client.patch("http://authentication-service:8000/edit_status", params={"status" : Status.FAILED, "email" : str(data.email)})
            response.raise_for_status()
        raise InternalClientError("Ошибка регистрации")
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
async def edit_user(request : Request, data : Annotated[UserEditSchema, Form()], service : UserService = Depends(get_service_dependency)):
    payload  = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])
    if data.email is not None and data.email != user.email:
        request_email = EmailRequest(old_email=user.email, new_email=data.email)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(url="http://authentication-service:8000/edit_email", json=request_email.model_dump(mode="json"))
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                if error.response.status_code == 409:
                    raise HTTPException(status_code=409, detail=[{"loc": ["body", "email"],"msg": "Этот логин уже занят"}])

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
async def edit_password(request: Request,service: UserService = Depends(get_service_dependency),
                        old_password: str = Form(), new_password: str = Form(), confirmed_password: str = Form()):
    payload = get_payload(request)
    user = await service.find_by_identity_id(payload["sub"])

    if new_password != confirmed_password:
        raise HTTPException(status_code=400,detail="Пароли не совпадают")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url="http://authentication-service:8000/get_identity",
                params={"identity_id": user.identity_id,"old_password": old_password,"new_password": new_password})
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401,detail="Неверный старый пароль")
        raise HTTPException(status_code=500,detail="Ошибка при смене пароля")
    response = JSONResponse({"success": True})
    response.delete_cookie("access_token")
    return response

@router.get("/get_all_users")
async def get_all_users(service : UserService = Depends(get_service_dependency),
                        internal_token : str = Header(..., alias="internal_token")):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(detail="Forbidden", status_code=403)
    users = await service.find_all_users()
    return [UserDto.model_validate(user).model_dump(mode="json") for user in users]

@router.get("/get_user_address")
async def get_user_address(identity_id : UUID, service : UserService = Depends(get_service_dependency)):
    user = await service.find_by_identity_id(identity_id)
    return UserInfo(
        name=user.name,
        surname=user.surname,
        email=user.email,
        phone=user.phone,
        birthday=user.birthday,
        city=user.address.city,
        postal_code=user.address.postal_code,
        street=user.address.street,
        house=user.address.house,
        apartment=user.address.apartment,
        created_at=user.created_at,
        updated_at=user.updated_at
    ).model_dump(mode="json")


