import uuid

from fastapi import APIRouter, Request
from fastapi.params import Header, Depends
from sqlalchemy import alias

from ..schema.restaurant_schema import RestaurantCreationDTO
from ..security.internal_security import verify_internal_token
from ..services.restaurant_service import RestaurantService
from ..dependencies.dependency import get_restaurant_dependency

router = APIRouter()

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
