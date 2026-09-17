from fastapi import APIRouter, Request, Depends
from starlette.responses import RedirectResponse

from ..dependencies.dependencies import get_order_service_dependency
from ..schema.order_item_schema import ListOrderDTO
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from uuid import UUID

from ..service.order_service import OrderService

router = APIRouter()

@router.post("/orders/create")
async def make_order(request : Request, data : ListOrderDTO,
                     service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    await service.create_order(data, client_id)
    return RedirectResponse(url="/payment/registered_users", status_code=303)