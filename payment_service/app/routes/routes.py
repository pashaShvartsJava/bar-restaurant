import httpx
import stripe
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from starlette.templating import Jinja2Templates

from ..models.payments import PaymentStatus
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
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    client_id = payload["sub"]
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
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    return templates.TemplateResponse("success_page.html", {"request" : request})

@router.get("/payment/cancel")
async def success_page(request : Request):
    payload = get_payload(request)
    required_roles(IdentityRole.USER, payload=payload)
    return templates.TemplateResponse("cancel_page.html", {"request" : request})
