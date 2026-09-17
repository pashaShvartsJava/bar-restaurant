from uuid import UUID

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..security.role.role import IdentityRole
from ..service.dish_service import MenuService
from ..service.category_service import CategoryService
from ..dependencies.dependencies import get_menu_service_dependency, get_category_service_dependency
from decimal import Decimal
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles

router = APIRouter()
templates = Jinja2Templates(directory="app/templates_menu")

@router.get("/menu_page", response_class=HTMLResponse)
async def get_menu_page(request: Request, category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    categories = await category_service.get_all_categories()
    return templates.TemplateResponse("menu.html", {"request":request, "categories" : categories})

@router.get("/menu_page/add_category", response_class=HTMLResponse)
async def get_categories_page(request: Request, category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    categories = await category_service.get_all_categories()
    return templates.TemplateResponse("add_category.html", {"request":request, "categories" : categories})

@router.post("/menu_page/add_category", response_class=HTMLResponse)
async def create_category(request : Request, category_name : str = Form(),
                              category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await category_service.create_category(category_name)
    return RedirectResponse(url="/menu_page/add_category", status_code=303)

@router.get("/menu_page/add_dish", response_class=HTMLResponse)
async def add_dish_page(request: Request, category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    categories = await category_service.get_all_categories()
    return templates.TemplateResponse("add_dish.html", {"request":request, "categories" : categories})

@router.post("/menu_page/add_dish", response_class=HTMLResponse)
async def create_dish(request : Request, dish_name : str = Form(...,),
                               price : Decimal = Form(...,),
                               description : str = Form(...,),
                               category_id : UUID = Form(...,),
                               image : UploadFile | None = File(None),
                               menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    image_url = None
    if image:
        upload_dir = "app/templates_menu/media/dishes"
        file_path = f"{upload_dir}/{image.filename}"
        with open(file_path, "wb") as file:
            file.write(await image.read())
        image_url = f"/media/dishes/{image.filename}"
    await menu_service.create_dish(dish_name, price, description, category_id, image_url)
    return RedirectResponse(url="/menu_page", status_code=303)

@router.patch("/menu_page/change_dish_status/{id}")
async def take_away_dish_from_menu(request : Request, id : int, menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await menu_service.update_dish_status(id)

@router.get("/menu_page/edit_dish/{id}")
async def show_edit_dish_page(request : Request, id : int, menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    dish = await menu_service.get_dish_by_id(id)
    return templates.TemplateResponse("edit_dish.html", {"request":request, "dish" : dish})

@router.post("/menu_page/edit_dish/{id}")
async def edit_dish(request : Request,
                    id : int,
                    dish_name: str | None = Form(None),
                    description : str | None= Form(None),
                    price : Decimal | None = Form(None),
                    image : UploadFile | None = File(None),
                    menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    image_url = None
    if image is not None and image.filename:
        upload_dir = "app/templates_menu/media/dishes"
        file_path = f"{upload_dir}/{image.filename}"
        with open(file_path, "wb") as file:
            file.write(await image.read())
        image_url = f"/media/dishes/{image.filename}"
    await menu_service.update_dish(id, dish_name, description, price, image_url)
    return RedirectResponse(url="/menu_page", status_code=303)

@router.get("/menu_page/orders/users")
async def menu_page_for_users(request : Request, category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    categories = await category_service.get_all_categories_for_users()
    return templates.TemplateResponse("menu_for_users.html", {"request" : request, "categories" : categories})