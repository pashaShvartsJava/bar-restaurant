import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, Header
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..security.internal_security import verify_internal_token
from ..security.role.role import IdentityRole
from ..service.dish_service import MenuService
from ..service.category_service import CategoryService
from ..dependencies.dependencies import get_menu_service_dependency, get_category_service_dependency, \
    get_restaurant_dependency, get_restaurant_dependency_by_id, get_currency_symbol
from decimal import Decimal
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles

router = APIRouter()
templates = Jinja2Templates(directory="app/templates_menu")

async def verify_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403)

@router.get("/menu_page", response_class=HTMLResponse)
async def get_menu_page(request: Request,
                        category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    currency_symbol = get_currency_symbol(restaurant.currency)
    categories = await category_service.get_all_categories(restaurant_id)
    return templates.TemplateResponse("menu.html", {"request" : request, "categories" : categories, "currency_symbol" : currency_symbol})

@router.get("/menu_page/add_category", response_class=HTMLResponse)
async def get_categories_page(request: Request,
                              category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    categories = await category_service.get_all_categories(restaurant_id)
    return templates.TemplateResponse("add_category.html", {"request":request,
                                                            "categories" : categories})

@router.post("/menu_page/add_category", response_class=HTMLResponse)
async def create_category(request : Request,
                          category_name : str = Form(),
                          category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant_id = payload.get("restaurant_id")
    await category_service.create_category(category_name, restaurant_id)
    return RedirectResponse(url="/menu_page/add_category", status_code=303)

@router.get("/menu_page/add_dish", response_class=HTMLResponse)
async def add_dish_page(request: Request,
                        category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    categories = await category_service.get_all_categories(restaurant_id)
    return templates.TemplateResponse("add_dish.html", {"request":request, "categories" : categories})

@router.post("/menu_page/add_dish", response_class=HTMLResponse)
async def create_dish(request : Request,
                      dish_name : str = Form(...,),
                               price : Decimal = Form(...,),
                               description : str = Form(...,),
                               category_id : UUID = Form(...,),
                               image : UploadFile | None = File(None),
                               menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant_id = payload.get("restaurant_id")
    image_url = None
    if image and image.filename:
        upload_dir = Path(f"app/templates_menu/media/dishes/{restaurant_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
        file_path = upload_dir / safe_filename
        file_path.write_bytes(await image.read())

        image_url = f"/media/dishes/{restaurant_id}/{safe_filename}"
    await menu_service.create_dish(dish_name, price, description, category_id, image_url, restaurant_id)
    return RedirectResponse(url="/menu_page", status_code=303)

@router.patch("/menu_page/change_dish_status/{id}")
async def take_away_dish_from_menu(request : Request, id : int, menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant_id = payload.get("restaurant_id")
    await menu_service.update_dish_status(id, restaurant_id)

@router.get("/menu_page/edit_dish/{id}")
async def show_edit_dish_page(request : Request, id : int, menu_service : MenuService = Depends(get_menu_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    dish = await menu_service.get_dish_by_id(id, restaurant_id)
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
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_csrf(request)
    restaurant_id = payload.get("restaurant_id")
    image_url = None
    if image is not None and image.filename:
        upload_dir = f"app/templates_menu/media/dishes/r/{restaurant_id}"
        file_path = f"{upload_dir}/{image.filename}"
        with open(file_path, "wb") as file:
            file.write(await image.read())
        image_url = f"/media/dishes/{image.filename}"
    await menu_service.update_dish(id, dish_name, description, price, image_url, restaurant_id)
    return RedirectResponse(url="/menu_page", status_code=303)

@router.get("/r/{slug}/menu_page/orders/users")
async def menu_page_for_users(request : Request,
                              slug : str,
                              category_service : CategoryService = Depends(get_category_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    categories = await category_service.get_all_categories_for_users(restaurant.id)
    currency_symbol = get_currency_symbol(restaurant.currency)
    return templates.TemplateResponse("menu_for_users.html", {"request" : request,
                                                              "categories" : categories,
                                                              "slug" : slug,
                                                              "restaurant" : restaurant,
                                                              "currency_symbol" : currency_symbol})


@router.get("/r/{slug}/delivery")
async def create_order_for_guest(request: Request,
                                 slug : str,
                                 category_service : CategoryService = Depends(get_category_service_dependency)):
    restaurant = await get_restaurant_dependency(slug)
    categories = await category_service.get_all_categories_for_users(restaurant.id)
    currency_symbol = get_currency_symbol(restaurant.currency)
    return templates.TemplateResponse("order_for_guest.html", {"request": request,
                                                               "categories" : categories,
                                                               "slug" : slug,
                                                               "restaurant" : restaurant,
                                                               "currency_symbol" : currency_symbol})

@router.get("/r/[slug}/menu_page/qr_code_menu")
async def qr_code_menu(request : Request,
                       slug : str,
                       table_number : int,
                       category_service : CategoryService = Depends(get_category_service_dependency)):
    restaurant = await get_restaurant_dependency(slug)
    categories = await category_service.get_all_categories_for_users(restaurant.id)
    return templates.TemplateResponse("qr_code_menu.html",
                                      {"request" : request,
                                       "categories" : categories,
                                       "table_number" : table_number,
                                       "slug" : slug,
                                       "restaurant" : restaurant})


@router.get("/menu_page/available_dishes")
async def get_all_available_dishes(request : Request,
                                   restaurant_id : UUID,
                                   service : MenuService = Depends(get_menu_service_dependency),
                                   internal_token : str = Header(..., alias="internal_token")):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    await verify_internal_token(internal_token)
    all_available_dishes = await service.get_all_available_dishes(restaurant_id)
    return all_available_dishes

