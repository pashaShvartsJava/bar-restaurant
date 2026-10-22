import uuid

import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.params import Header
from starlette.templating import Jinja2Templates
from ..schemas.subscription_schema import SubscriptionCheckoutDTO
from ..security.internal_security import verify_internal_token
from ..dependencies.dependencies import get_subscription_service_dependency
from ..config.config import settings
from ..service.subscription_service import SubscriptionService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
INTERNAL_TOKEN=settings.internal_token

@router.post("/payment/subscription")
async def subscription_payment(request : Request,
                               restaurant_id : str,
                               data : SubscriptionCheckoutDTO,
                               internal_token : str = Header(..., alias="internal_token"),
                               service : SubscriptionService = Depends(get_subscription_service_dependency)):
    await verify_internal_token(internal_token)
    subscription, checkout_url = await service.create_subscription(data, uuid.UUID(restaurant_id))
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
    elif event["type"] == "customer.subscription.updated":
        await sub_service.handle_subscription_updated(event)
    elif event["type"] == "customer.subscription.deleted":
        await sub_service.handle_subscription_deleted(event)
    elif event["type"] == "invoice.payment_failed":
        await sub_service.handle_invoice_payment_failed(event)
    return {"status": "ok"}
