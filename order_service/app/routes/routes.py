from fastapi import APIRouter, Request, Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..dependencies.dependencies import get_order_service_dependency
from ..models.orders import OrderStatus
from ..schema.delivery_address_schema import DeliveryAddressDTO
from ..schema.order_item_schema import ListOrderDTO
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from uuid import UUID

from ..service.order_service import OrderService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/orders/get_orders")
async def get_all_orders(request : Request, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    orders = await service.get_all_orders()
    return templates.TemplateResponse("all_orders.html", {"request" : request, "orders" : orders})

@router.post("/orders/create")
async def make_order(request : Request, data : ListOrderDTO,
                     service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    await service.create_order(data, client_id)
    return RedirectResponse(url="/users/confirm_address", status_code=303)

@router.post("/orders/cancel_order/before_payment")
async def cancel_order_before_payment(request : Request, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    await service.cancel_order_before_payment(client_id)
    return RedirectResponse(url="/my_profile/users", status_code=303)

@router.post("/orders/confirm_address")
async def create_delivering_address(request : Request,
                                    data : DeliveryAddressDTO,
                                    service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    order = await service.get_pending_by_client_id(client_id)
    await service.create_order_address(order.id, data)
    await service.update_order_status(client_id, OrderStatus.CONFIRMED_ADDRESS)
    return RedirectResponse(url="/payment/registered_users")