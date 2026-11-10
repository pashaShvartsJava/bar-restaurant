import uuid
from uuid import UUID

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

PORTAL_CONFIGURATION_ID: str | None = None

def get_or_create_portal_configuration() -> str:
    global PORTAL_CONFIGURATION_ID
    if PORTAL_CONFIGURATION_ID:
        return PORTAL_CONFIGURATION_ID
    configurations = stripe.billing_portal.Configuration.list(limit=100)
    for cfg in configurations.auto_paging_iter():
        allowed = (
            cfg.features
            and cfg.features.customer_update
            and cfg.features.customer_update.enabled
            and "tax_id" in (cfg.features.customer_update.allowed_updates or []))
        if allowed:
            PORTAL_CONFIGURATION_ID = cfg.id
            return cfg.id
    configuration = stripe.billing_portal.Configuration.create(
        features={
            "customer_update": {"enabled": True, "allowed_updates": ["email", "tax_id"]},
            "invoice_history": {"enabled": True}},
        business_profile={"privacy_policy_url": "https://localhost:8443/privacy",
                          "terms_of_service_url": "https://localhost:8443/terms"})
    PORTAL_CONFIGURATION_ID = configuration.id
    return configuration.id

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
        session = event["data"]["object"].to_dict()
        if "sub_idempotency_key" not in session.get("metadata", {}):
            return {"status": "ignored"}
        await sub_service.handle_subscription_webhook(event)
    elif event["type"] in ("customer.subscription.created", "customer.subscription.updated"):
        await sub_service.handle_subscription_updated(event)
    elif event["type"] == "customer.subscription.deleted":
        await sub_service.handle_subscription_deleted(event)
    elif event["type"] == "invoice.payment_failed":
        await sub_service.handle_invoice_payment_failed(event)
    elif event["type"] in ("customer.tax_id.created", "customer.tax_id.updated", "customer.tax_id.deleted"):
        await sub_service.handle_tax_id_webhook(event)
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
    key = request.query_params.get("key")
    return templates.TemplateResponse("subscription_success_page.html", {"request" : request,
                                                                         "subscription_number" : subscription_number,
                                                                         "key" : key})

@router.get("/payment/subscription/cancel")
async def subscription_success_page(request : Request):
    return templates.TemplateResponse("subscription_cancel_page.html", {"request" : request})

@router.get("/subscription/portal")
async def create_portal_session(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    customer_id = payload.get("sub")
    restaurant_id = payload.get("restaurant_id")
    subscription = await sub_service.get_subscription_by_owner_id(customer_id, restaurant_id)
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No active subscription or currently subscription has a trialing period")
    try:
        configuration_id = get_or_create_portal_configuration()
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url="http://localhost:8443/admin_panel",
            configuration=configuration_id)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": session.url}

@router.get("/subscription/get_percentage_commission")
async def get_restaurant_percentage_commission(restaurant_id : str,
                                               internal_token : str = Header(..., alias="internal_token"),
                                               sub_service : SubscriptionService = Depends(get_subscription_service_dependency)):
    await verify_internal_token(internal_token)
    active_subscription = await sub_service.get_restaurant_percentage_commission(uuid.UUID(restaurant_id))
    return active_subscription.order_commission_percent

@router.get("/subscription/get_vat_status")
async def get_subscription_vat_status(restaurant_id : str,
                                      internal_token : str = Header(..., alias="internal_token"),
                                      sub_service : SubscriptionService = Depends(get_subscription_service_dependency)):
    await verify_internal_token(internal_token)
    active_subscription = await sub_service.get_subscription_by_restaurant_id(uuid.UUID(restaurant_id))
    return active_subscription.vat_status.value

