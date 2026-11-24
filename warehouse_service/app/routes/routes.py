import uuid
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..config.config import settings
from ..dependencies.dependencies import get_restaurant_dependency_by_id, verify_restaurant_status, \
    get_service_dependency
from ..models.products_model import Unit
from ..security.authorization.authorization import required_roles
from ..security.jwt.jwt import get_payload
from ..security.role.role import IdentityRole
from ..service.product_service import ProductService

INTERNAL_TOKEN = settings.internal_token
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def verify_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403)

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
                      is_active : bool,
                      product_id : int,
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