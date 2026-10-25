import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.params import Header
from starlette.templating import Jinja2Templates
from ..schemas.subscription_schema import SubscriptionCheckoutDTO
from ..security.authorization.authorization import required_roles
from ..security.internal_security import verify_internal_token
from ..dependencies.dependencies import get_subscription_service_dependency
from ..config.config import settings
from ..security.jwt.jwt import get_payload
from ..security.role.role import IdentityRole
from ..service.subscription_service import SubscriptionService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
INTERNAL_TOKEN=settings.internal_token

@router.post("/payment/subscription")
async def subscription_payment(data : SubscriptionCheckoutDTO,
                               internal_token : str = Header(..., alias="internal_token"),
                               service : SubscriptionService = Depends(get_subscription_service_dependency)):
    await verify_internal_token(internal_token)
    subscription, checkout_url = await service.create_subscription(data)
    return {"subscription_id" : subscription.id, "checkout_url" : checkout_url}

@router.post("/subscription/webhook")
async def stripe_subscription_webhook(request: Request, sub_service : SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        event = sub_service.stripe_service.construct_webhook_subscription_event(payload, signature)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")
    if event["type"] == "checkout.session.completed":
        await sub_service.handle_subscription_webhook(event)
    elif event["type"] in ("customer.subscription.created", "customer.subscription.updated"):
        await sub_service.handle_subscription_updated(event)
    elif event["type"] == "customer.subscription.deleted":
        await sub_service.handle_subscription_deleted(event)
    elif event["type"] == "invoice.payment_failed":
        await sub_service.handle_invoice_payment_failed(event)
    return {"status": "ok"}

@router.delete("/payment/subscription/saga_delete")
async def delete_saga_subscription(sub_idempotency_key : str,
                                   internal_token : str = Header(..., alias="internal_token"),
                                   sub_service : SubscriptionService = Depends(get_subscription_service_dependency)):
    await verify_internal_token(internal_token)
    await sub_service.delete_saga_subscription(sub_idempotency_key)

@router.get("/payment/subscription/success")
async def subscription_success_page(request : Request):
    subscription_number = request.query_params.get("subscription_number")
    return templates.TemplateResponse("subscription_success_page.html", {"request" : request, "subscription_number" : subscription_number})

@router.get("/payment/subscription/cancel")
async def subscription_success_page(request : Request):
    return templates.TemplateResponse("subscription_cancel_page.html", {"request" : request})

@router.post("/subscription/portal")
async def create_portal_session(request :Request, stripe_customer_id: str):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    session = stripe.billing_portal.Session.create(customer=stripe_customer_id, return_url="https://localhost:8443/admin_panel")
    return {"url": session.url}
