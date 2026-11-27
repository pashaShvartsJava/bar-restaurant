import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, Header
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..config.config import settings
from ..dependencies.dependencies import get_restaurant_dependency_by_id, verify_restaurant_status, \
    get_service_dependency, get_admin_data, get_reserved_products_service_dependency
from ..models.products_model import Unit
from ..schema.order_item_schema import ListOrderDTO, ListOrderGuestDTO
from ..security.authorization.authorization import required_roles
from ..security.internal_security import verify_internal_token
from ..security.jwt.jwt import get_payload
from ..security.role.role import IdentityRole
from ..service.product_service import ProductService
from ..service.reserved_products_service import ReservedProductsService
from ..exceptions.exceptions import InsufficientStockError

INTERNAL_TOKEN = settings.internal_token
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def verify_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403, detail="CSRF protection was triggered.")

@router.get("/warehouse")
async def get_warehouse_page(request : Request, service : ProductService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    products = await service.get_all_products()
    return templates.TemplateResponse("warehouse_page.html", {"request" : request, "products" : products})

@router.post("/warehouse/add_product")
async def add_new_product(request : Request,
                          name : str = Form(...,),
                          unit : Unit = Form(...,),
                          description : str | None = Form(None),
                          image : UploadFile | None = File(None),
                          service : ProductService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    await verify_csrf(request)
    image_url = None
    if image and image.filename:
        upload_dir = Path(f"app/templates/media/products/{restaurant_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
        file_path = upload_dir / safe_filename
        file_path.write_bytes(await image.read())
        image_url = f"/media/products/{restaurant_id}/{safe_filename}"
    await service.create_product(name, unit, description, restaurant_id, image_url)
    return RedirectResponse(url="/warehouse", status_code=303)

@router.post("/warehouse/edit_product/{product_id}")
async def eit_product(request : Request,
                      product_id : int,
                      is_active : bool = Form(False),
                      name : str | None = Form(None),
                      unit : Unit | None = Form(None),
                      description : str | None = Form(None),
                      image : UploadFile | None = File(None),
                      service : ProductService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    await verify_csrf(request)
    image_url = None
    if image and image.filename:
        upload_dir = Path(f"app/templates/media/products/{restaurant_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
        file_path = upload_dir / safe_filename
        file_path.write_bytes(await image.read())
        image_url = f"/media/products/{restaurant_id}/{safe_filename}"
    await service.update_product(product_id, name, unit, description, restaurant_id, image_url, is_active)
    return RedirectResponse(url="/warehouse", status_code=303)

@router.post("/warehouse/add_supply/{product_id}")
async def add_supply(request : Request,
                     product_id : int,
                     quantity : Decimal = Form(...,),
                     service : ProductService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    identity_id = payload.get("sub")
    token = request.cookies.get("access_token")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    await verify_csrf(request)
    admin_data = await get_admin_data(restaurant_id, identity_id, token)
    await service.create_supply(product_id, restaurant_id, quantity, admin_data)
    return RedirectResponse(url="/warehouse", status_code=303)

@router.get("/warehouse/supplies")
async def supplies_history(request : Request, service : ProductService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    supplies = await service.find_all_supplies()
    return templates.TemplateResponse("supplies_page.html", {"request" : request, "supplies" : supplies})

@router.patch("/warehouse/edit_supply/{supply_id}")
async def edit_supply(request : Request,
                      supply_id : int,
                      quantity : Decimal = Form(...,),
                      reason : str = Form(...,),
                      service : ProductService = Depends(get_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    await verify_csrf(request)
    await service.fix_supply(supply_id, restaurant_id, quantity, reason)
    return RedirectResponse(url="/warehouse/supplies", status_code=303)

@router.post("/warehouse/check_or_reserve_products_from_warehouse")
async def check_or_reserve_products_from_warehouse(restaurant_id : str,
                                                   order_number : str,
                                                   data : ListOrderDTO | ListOrderGuestDTO,
                                                   service : ReservedProductsService = Depends(get_reserved_products_service_dependency),
                                                   internal_token : str = Header(..., alias="internal_token")):
    await verify_internal_token(internal_token)
    result = await service.create_reserved_products(uuid.UUID(restaurant_id), data, order_number)
    if result.get("message") == "InsufficientStockProductsError":
        raise HTTPException(status_code=409, detail="Недостаточно продуктов для создания заказа")
    return result.get("message")


