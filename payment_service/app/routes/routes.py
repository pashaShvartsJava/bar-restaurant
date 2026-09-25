from uuid import UUID

import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from starlette.templating import Jinja2Templates

from ..schemas.payment_schema import PaymentDTO
from ..security.authorization.authorization import required_roles
from ..security.jwt.jwt import get_payload
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_payment_service_dependency
from ..service.payment_service import PaymentService
from ..config.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
INTERNAL_TOKEN=settings.internal_token

@router.post("/payment/create")
async def create_payment(request : Request,
                         data: PaymentDTO,
                         service : PaymentService = Depends(get_payment_service_dependency)):
    access_token = request.cookies.get("access_token")
    if access_token is not None:
        payload = get_payload(request)
        client_id = UUID(payload["sub"])
    else:
        guest_client_id = request.cookies.get("guest_client_id")
        if guest_client_id is None:
            raise HTTPException(status_code=401, detail="Client ID not found")
        try:
            client_id = UUID(guest_client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid guest client ID")
    if data.client_id != client_id:
        raise HTTPException(detail="invalid customer id", status_code=403)
    payment, checkout_url = await service.create_payment(data, client_id)
    return {"payment_id": payment.id,  "checkout_url": checkout_url}

@router.post("/payment/webhook")
async def stripe_webhook(request: Request, service: PaymentService = Depends(get_payment_service_dependency)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        event = service.stripe_service.construct_webhook_event(payload, signature)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")
    await service.handle_webhook(event)
    return {"status": "ok"}

@router.get("/payment/success")
async def success_page(request : Request):
    return templates.TemplateResponse("success_page.html", {"request" : request})

@router.get("/payment/cancel")
async def success_page(request : Request):
    return templates.TemplateResponse("cancel_page.html", {"request" : request})

