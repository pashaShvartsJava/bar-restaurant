import uuid
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.params import Header
from starlette.templating import Jinja2Templates

from ..schemas.subscription_schema import SubscriptionCheckoutDTO, PlanId, STRIPE_PRICE_IDS, SubscriptionDataDTO
from ..security.authorization.authorization import required_roles
from ..security.internal_security import verify_internal_token
from ..dependencies.dependencies import get_subscription_service_dependency
from ..config.config import settings
from ..security.jwt.jwt import get_payload
from ..security.role.role import IdentityRole
from ..service.subscription_service import SubscriptionService
from ..service.stripe_tax_manager_rate import StripeTaxRateManager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
INTERNAL_TOKEN=settings.internal_token

PORTAL_CONFIGURATION_ID: str | None = None


async def get_price_id_for_plan(plan_id: str) -> str | None:
    return STRIPE_PRICE_IDS.get(plan_id)

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
    print("DEBUG: Router with webhook handling ran ::::::")
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
        print("DEBUG: elif with update webhook ran ::::::")
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

@router.get("/subscription/management")
async def subscription_management_page(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency),):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    customer_id = payload.get("sub")
    restaurant_id = payload.get("restaurant_id")
    subscription = await sub_service.get_subscription_by_owner_id(customer_id, restaurant_id)
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No active subscription or currently subscription has a trialing period")
    return templates.TemplateResponse("subscription_management.html",
                                      {"request": request, "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY})

@router.get("/subscription/current")
async def get_current_subscription(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub:
        raise HTTPException(404, "No subscription")
    cancel_at_period_end = False
    if sub.stripe_subscription_id:
        try:
            stripe_sub = await stripe.Subscription.retrieve_async(sub.stripe_subscription_id)
            cancel_at_period_end = stripe_sub.cancel_at_period_end
        except stripe.StripeError:
            pass
    return {
        "plan_id": sub.plan_id.value if hasattr(sub.plan_id, "value") else sub.plan_id,
        "plan_name": sub.plan_name,
        "status": sub.status.value if hasattr(sub.status, "value") else sub.status,
        "cancel_at_period_end": cancel_at_period_end,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "vat_id": sub.vat_id,
        "vat_status": sub.vat_status.value if hasattr(sub.vat_status, "value") else sub.vat_status,
        "address": {
            "line1": getattr(sub, "address_line1", None),
            "city": getattr(sub, "address_city", None),
            "postal_code": getattr(sub, "address_postal_code", None),
            "country": sub.country} if getattr(sub, "country", None) else None}

@router.get("/subscription/invoices")
async def get_invoices(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_customer_id:
        return []
    invoices = await stripe.Invoice.list_async(customer=sub.stripe_customer_id, limit=20)
    result = []
    for inv in invoices.data:
        result.append({
            "date": datetime.fromtimestamp(inv.created, tz=timezone.utc).strftime("%d.%m.%Y"),
            "total": f"{inv.total / 100:.2f}",
            "currency": inv.currency.upper(),
            "hosted_invoice_url": inv.hosted_invoice_url})
    return result

@router.post("/subscription/setup-intent")
async def create_setup_intent(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency),):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(404, "No subscription")
    setup_intent = await stripe.SetupIntent.create_async(customer=sub.stripe_customer_id, payment_method_types=["card", "sepa_debit"])
    return {"client_secret": setup_intent.client_secret}

@router.post("/subscription/attach-payment-method")
async def attach_payment_method(request: Request,
                                body: dict,
                                sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    payment_method_id = body.get("payment_method_id")
    if not payment_method_id:
        raise HTTPException(400, "payment_method_id required")
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(404, "No subscription")
    await stripe.PaymentMethod.attach_async(payment_method_id, customer=sub.stripe_customer_id)
    await stripe.Customer.modify_async(sub.stripe_customer_id, invoice_settings={"default_payment_method": payment_method_id})
    return {"status": "ok"}

@router.post("/subscription/change-plan")
async def change_plan(request: Request,
                      body: dict,
                      sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    plan_id = body.get("plan_id")
    if not plan_id:
        raise HTTPException(400, "plan_id required")
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(404, "No subscription")
    try:
        stripe_sub = await stripe.Subscription.retrieve_async(sub.stripe_subscription_id)
        current_item_id = stripe_sub["items"]["data"][0]["id"]
        new_price_id = await get_price_id_for_plan(plan_id)
        if not new_price_id:
            raise HTTPException(400, "Invalid plan")
        tax_manager = StripeTaxRateManager(client=sub_service.stripe_service.client)
        tax_rate_id = await tax_manager.get_or_create_tax_rate(sub.country)
        updated_sub = await stripe.Subscription.modify_async(sub.stripe_subscription_id,
                                                             items=[{"id": current_item_id,
                                                                     "price": new_price_id}],
                                                             proration_behavior="always_invoice",
                                                             default_tax_rates=[tax_rate_id])
        invoices = await stripe.Invoice.list_async(subscription=updated_sub.id, status="open", limit=1)
        if invoices.data:
            return {"checkout_url": invoices.data[0]["hosted_invoice_url"]}
        return {"status": "ok"}
    except stripe.StripeError as e:
        raise HTTPException(400, str(e))


@router.post("/subscription/update-vat")
async def update_vat(request: Request, body: dict, sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    vat_id = (body.get("vat_id") or "").strip().upper()
    if not vat_id:
        raise HTTPException(400, "vat_id required")
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub:
        raise HTTPException(404, "No subscription")
    result = await sub_service.update_vat(sub, vat_id)
    return result

@router.post("/subscription/update-address")
async def update_address(request: Request, body: dict, sub_service: SubscriptionService = Depends(get_subscription_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(404, "No subscription")
    await stripe.Customer.modify_async(
        sub.stripe_customer_id,
        address={
            "line1": body.get("line1"),
            "city": body.get("city"),
            "postal_code": body.get("postal_code"),
            "country": body.get("country")})
    return {"status": "ok"}

@router.post("/subscription/cancel")
async def cancel_subscription(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency),):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(404, "No subscription")
    await stripe.Subscription.modify_async(sub.stripe_subscription_id, cancel_at_period_end=True)
    return {"status": "ok"}

@router.post("/subscription/resume")
async def resume_subscription(request: Request, sub_service: SubscriptionService = Depends(get_subscription_service_dependency),):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    sub = await sub_service.get_subscription_by_owner_id(payload["sub"], payload["restaurant_id"])
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(404, "No subscription")
    await stripe.Subscription.modify_async(sub.stripe_subscription_id, cancel_at_period_end=False)
    return {"status": "ok"}

@router.get("/subscription/get_subscription")
async def get_subscription_dto(restaurant_id : str,
                               internal_token : str = Header(..., alias="internal_token"),
                               service : SubscriptionService = Depends(get_subscription_service_dependency)):
    await verify_internal_token(internal_token)
    subscription = await service.get_subscription_by_restaurant_id(uuid.UUID(restaurant_id))
    return SubscriptionDataDTO.model_validate(subscription)


