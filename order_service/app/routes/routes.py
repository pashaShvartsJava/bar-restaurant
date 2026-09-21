from datetime import date
from decimal import Decimal
from multiprocessing.connection import address_type

import httpx
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

@router.get("/orders/history")
async def orders_history_page(request : Request, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    orders = await service.get_all_orders_history()
    return templates.TemplateResponse("old_orders.html", {"request": request, "orders": orders})

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

@router.get("/orders/get_orders/search_or_sorting")
async def search_and_sorting(request : Request,
                             search: str | None = None,
                             status: OrderStatus | None = None,
                             date_from: date | None = None,
                             date_to: date | None = None,
                             sum_from: Decimal | None = None,
                             sum_to: Decimal | None = None,
                             sort: str = "created_desc",
                             service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    orders = await service.search_or_sort_orders(search, status, date_from, date_to, sum_from, sum_to, sort)
    return templates.TemplateResponse("all_orders.html", {"request" : request, "orders" : orders})

@router.get("/orders/get_customer_orders")
async def get_user_orders(request : Request, identity_id : UUID, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    orders = await service.find_order_by_client_id(identity_id)
    return orders

@router.get("/orders/my_history_orders")
async def get_user_history_orders(request : Request, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    history_orders = await service.get_user_history_orders(client_id)
    return templates.TemplateResponse("user_history_orders.html", {"request" : request, "orders" : history_orders})

@router.get("/orders/get_user_active_orders")
async def get_my_active_orders(request : Request, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    active_orders = await service.get_user_active_orders(client_id)
    return active_orders


@router.get("/orders/{order_id}")
async def get_order_info(request : Request, order_id : int, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    order = await service.get_order_by_id(order_id)
    return templates.TemplateResponse("order_info.html", {"request" : request, "order" : order})




