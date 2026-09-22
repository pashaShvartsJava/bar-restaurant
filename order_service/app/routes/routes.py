from datetime import date
from decimal import Decimal

import httpx
from fastapi import APIRouter, Request, Depends, Header, HTTPException
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..dependencies.dependencies import get_order_service_dependency
from ..models.orders import OrderStatus
from ..schema.delivery_address_schema import DeliveryAddressDTO
from ..schema.order_item_schema import ListOrderDTO
from ..schema.orders_schema import StatusDTO
from ..schema.payment_schema import PaymentDTO
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from uuid import UUID

from ..service.order_service import OrderService
from ..config.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
INTERNAL_TOKEN=settings.internal_token

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

@router.patch("/orders/{order_number}/status")
async def change_order_status(request : Request,
                              order_number : str ,
                              data : StatusDTO,
                              service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    await service.change_order_status(UUID(order_number), data.status)

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
    updated_order = await service.update_order_status(client_id, OrderStatus.CONFIRMED_ADDRESS)
    data = PaymentDTO(
        order_id=order.id,
        order_number=order.order_number,
        sum=order.sum
    )
    if updated_order.status==OrderStatus.CONFIRMED_ADDRESS:
        async with httpx.AsyncClient() as client:
            response = await client.post(url="http://payment-service:8008/payment/create",
                                         json=data.model_dump(mode="json"),
                                         cookies={"access_token" : request.cookies.get("access_token")})
            response.raise_for_status()
            payment_data = response.json()
        return RedirectResponse(url=payment_data["checkout_url"], status_code=303)
    return None


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

@router.get("/orders/get_user_last_completed_order")
async def get_last_user_order(request : Request, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = UUID(payload["sub"])
    last_order = await service.get_user_last_completed_order(client_id)
    return last_order


@router.get("/orders/{order_id}")
async def get_order_info(request : Request, order_id : int, service : OrderService = Depends(get_order_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    order = await service.get_order_by_id(order_id)
    return templates.TemplateResponse("order_info.html", {"request" : request, "order" : order})

@router.post("/orders/mark_order_as_paid")
async def mark_order_as_paid(client_id : UUID,
                             internal_token : str = Header(..., alias="internal_token"),
                             service : OrderService = Depends(get_order_service_dependency)):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(detail="Forbidden", status_code=403)
    await service.mark_order_as_paid(client_id, OrderStatus.PAID)





