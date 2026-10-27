import uuid

from fastapi import APIRouter, Request, HTTPException
from fastapi.params import Header, Depends
from uuid import UUID

from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from ..schema.restaurant_schema import RestaurantCreationDTO, KeyDTO
from ..security.internal_security import verify_internal_token
from ..services.restaurant_service import RestaurantService
from ..dependencies.dependency import get_restaurant_dependency

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/r/{slug}", response_class=HTMLResponse)
async def restaurant_page(request: Request,
                    slug : str,
                    service : RestaurantService = Depends(get_restaurant_dependency)):
    restaurant = await service.get_restaurant_by_slug(slug)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return templates.TemplateResponse("main_page.html", context={"request": request, "restaurant" : restaurant})

@router.get("/restaurants")
async def all_restaurants(request : Request, service : RestaurantService = Depends(get_restaurant_dependency)):
    restaurants = await service.get_all_restaurants()
    return templates.TemplateResponse("all_restaurants.html", {"request" : request, "restaurants" : restaurants})

@router.post("/restaurants/add_restaurant")
async def create_restaurant(data : RestaurantCreationDTO,
                            internal_token : str = Header(..., alias="internal_token"),
                            service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.create_restaurant(data)
    return restaurant.id

@router.post("/restaurants/delete_saga_restaurant")
async def delete_saga_restaurant( restaurant_id : str,
                                  internal_token : str = Header(..., alias="internal_token"),
                                  service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    await service.delete_saga_restaurant(uuid.UUID(restaurant_id))

@router.post("/restaurants/get_restaurant_status")
async def get_restaurant_status(data : KeyDTO,
                                internal_token : str = Header(..., alias="internal_token"),
                                service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant_status = await service.get_status_by_owner_and_id(data)
    return restaurant_status

@router.delete("/restaurants/delete_saga_membership")
async def delete_saga_membership(identity_id : str,
                                 internal_token : str = Header(..., alias="internal_token"),
                                 service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    await service.delete_saga_membership(uuid.UUID(identity_id))

@router.get("/restaurants/get_restaurant_id")
async def get_restaurant(identity_id : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    membership = await service.get_membership_by_identity_id(uuid.UUID(identity_id))
    return membership.restaurant_id

@router.get("/restaurants/get_restaurant_id_by_slug")
async def get_restaurant_by_slug(slug : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.get_restaurant_by_slug(slug)
    return restaurant.restaurant_id

@router.post("/restaurants/add_membership")
async def add_membership(identity_id : str,
                         restaurant_id : str,
                         role : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    await service.create_membership(uuid.UUID(identity_id), uuid.UUID(restaurant_id), role)
