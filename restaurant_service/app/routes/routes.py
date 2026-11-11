from ..config.config import settings
import stripe
import json
import uuid
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID
import httpx
from fastapi import APIRouter, Request, HTTPException, UploadFile
from fastapi.params import Header, Depends, Form, File

from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..models.restaurant_model import RestaurantStatus, Restaurant
from ..schema.constructor_schema import UpdateRestaurantDTO
from ..schema.subscription_schema import SubscriptionCheckoutDTO
from ..security.authorization.authorization import required_role, required_roles
from ..security.jwt.jwt import get_payload
from ..schema.restaurant_schema import RestaurantCreationDTO, KeyDTO, RestaurantConstructorDTO, \
    RestaurantForUserProfileDTO
from ..security.internal_security import verify_internal_token, verify_csrf
from ..security.role.role import IdentityRole
from ..services.restaurant_service import RestaurantService
from ..dependencies.dependency import get_restaurant_dependency

INTERNAL_TOKEN = settings.internal_token
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/r/{slug}", response_class=HTMLResponse)
async def restaurant_page(request: Request,
                    slug : str,
                    service : RestaurantService = Depends(get_restaurant_dependency)):
    restaurant = await service.get_restaurant_by_slug(slug)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return templates.TemplateResponse("main_page.html", context={"request": request, "restaurant" : restaurant})

@router.get("/restaurants")
async def all_restaurants(request : Request, service : RestaurantService = Depends(get_restaurant_dependency)):
    restaurants = await service.get_all_restaurants()
    return templates.TemplateResponse("all_restaurants.html", {"request" : request, "restaurants" : restaurants})

@router.get("/restaurants/get_restaurants_for_user_profile")
async def all_restaurants(request : Request,
                          internal_token : str = Header(..., alias="internal_token"),
                          service : RestaurantService = Depends(get_restaurant_dependency)):
    payload = get_payload(request)
    required_role(IdentityRole.USER, payload)
    await verify_internal_token(internal_token)
    restaurants = await service.get_all_restaurants()
    return [
        RestaurantForUserProfileDTO(
            slug=r.slug,
            restaurant_name=r.restaurant_name,
            city=r.city,
            short_description=r.short_description,
            photo_url=r.photo_url) for r in restaurants]

@router.post("/restaurants/add_restaurant")
async def create_restaurant(data : RestaurantCreationDTO,
                            internal_token : str = Header(..., alias="internal_token"),
                            service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.create_restaurant(data)
    return restaurant.id

@router.post("/restaurants/delete_saga_restaurant")
async def delete_saga_restaurant( restaurant_id : str,
                                  internal_token : str = Header(..., alias="internal_token"),
                                  service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    await service.delete_saga_restaurant(uuid.UUID(restaurant_id))

@router.post("/restaurants/get_restaurant_status")
async def get_restaurant_status(data : KeyDTO,
                                internal_token : str = Header(..., alias="internal_token"),
                                service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant_status = await service.get_status_by_owner_and_id(data)
    return restaurant_status

@router.delete("/restaurants/delete_saga_membership")
async def delete_saga_membership(identity_id : str,
                                 internal_token : str = Header(..., alias="internal_token"),
                                 service : RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    await service.delete_saga_membership(uuid.UUID(identity_id))

@router.get("/restaurants/get_restaurant_id")
async def get_restaurant(identity_id : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    membership = await service.get_membership_by_identity_id(uuid.UUID(identity_id))
    return membership.restaurant_id

@router.get("/restaurants/get_restaurant_by_slug")
async def get_restaurant_by_slug(slug : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.get_restaurant_by_slug(slug)
    return RestaurantConstructorDTO.model_validate(restaurant, from_attributes=True)

@router.get("/restaurants/get_restaurant_by_id")
async def get_restaurant_by_restaurant_id(restaurant_id : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.get_restaurant_by_id(uuid.UUID(restaurant_id))
    return RestaurantConstructorDTO.model_validate(restaurant, from_attributes=True)

@router.get("/restaurants/get_restaurant_by_stripe_account_id")
async def get_restaurant_by_stripe_account_id(stripe_account_id : str,
                                              internal_token: str = Header(..., alias="internal_token"),
                                              service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.get_restaurant_by_stripe_account_id(uuid.UUID(stripe_account_id))
    return RestaurantConstructorDTO.model_validate(restaurant, from_attributes=True)


@router.post("/restaurants/add_membership")
async def add_membership(identity_id : str,
                         restaurant_id : str,
                         role : str,
                         internal_token: str = Header(..., alias="internal_token"),
                         service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    await service.create_membership(uuid.UUID(identity_id), uuid.UUID(restaurant_id), role)

@router.get("/restaurants/find_by_name")
async def get_res_by_name_and_renew_subscription(name : str,
                                                 plan_id : str,
                                                 billing_period : str,
                                                 price : Decimal,
                                                 order_commission_percent : Decimal,
                                                 service : RestaurantService = Depends(get_restaurant_dependency)):
    restaurant = await service.get_restaurant_by_name(name)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Ресторан не найден.")
    if restaurant.status in (RestaurantStatus.ACTIVE, RestaurantStatus.PENDING, RestaurantStatus.CLOSED):
        return {"error": "Подписка данного заведения либо всё ещё активна, "
                     "либо заведение полностью закрыто. "
                     "На данный момент продление подписки невозможно.",
            "status": restaurant.status.value}
    async with httpx.AsyncClient() as client:
        key_response = await client.get( url="http://authentication-service:8000/get_auth_key",
                                         params={"restaurant_id": restaurant.id},
                                         headers={"internal_token": INTERNAL_TOKEN})
    if key_response.is_error:
        return {"error": "Ошибка сервера. Повторите операцию позже.",
                "status": restaurant.status.value}
    key = key_response.json()
    subscription_checkout_dto = SubscriptionCheckoutDTO(
        user_id=restaurant.memberships.identity_id,
        restaurant_id=restaurant.id,
        sub_idempotency_key=uuid.uuid4(),
        email=restaurant.email,
        plan_id=plan_id,
        billing_period=billing_period,
        trial_days=0,
        price=price,
        order_commission_percent=order_commission_percent,
        currency="EUR",
        key=key)
    async with httpx.AsyncClient() as client:
        response = await client.post(url="http://payment-service:8008/payment/subscription",
                                     headers={"internal_token": INTERNAL_TOKEN},
                                     json=subscription_checkout_dto.model_dump(mode="json"))
    if response.is_error:
        return { "error": "Не удалось создать подписку. Попробуйте ещё раз.", "status": restaurant.status.value}
    data = response.json()
    checkout_url = data.get("checkout_url") or data.get("url")
    if not checkout_url:
        return { "error": "Сервер не вернул ссылку на оплату.", "status": restaurant.status.value,}
    return { "checkout_url": checkout_url, "status": restaurant.status.value}

@router.get("/restaurants/constructor")
async def get_constructor_page(request : Request, service : RestaurantService = Depends(get_restaurant_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await service.get_restaurant_by_id(restaurant_id)
    return templates.TemplateResponse("constructor.html", {"request" : request, "restaurant" : restaurant})

@router.patch("/restaurants/constructor")
async def get_constructor_page(request : Request,
                               country: Annotated[str, Form(...)],
                               city: Annotated[str, Form(...)],
                               address: Annotated[str, Form(...)],
                               timezone: Annotated[str, Form(...)],
                               restaurant_name: Annotated[str, Form(...)],
                               slug: Annotated[str, Form(...)],
                               slogan: Annotated[Optional[str], Form()] = None,
                               tagline: Annotated[Optional[str], Form()] = None,
                               short_description: Annotated[Optional[str], Form()] = None,
                               description: Annotated[Optional[str], Form()] = None,
                               about_title: Annotated[Optional[str], Form()] = None,
                               currency: Annotated[str, Form()] = "EUR",
                               phone: Annotated[Optional[str], Form()] = None,
                               email: Annotated[Optional[str], Form()] = None,
                               instagram_url: Annotated[Optional[str], Form()] = None,
                               working_hours: Annotated[Optional[str], Form()] = None,
                               accepts_reservations: Annotated[bool, Form()] = True,
                               accepts_delivery: Annotated[bool, Form()] = True,
                               accepts_orders_on_site: Annotated[bool, Form()] = True,
                               remove_photo: Annotated[bool, Form()] = False,
                               photo: Annotated[Optional[UploadFile], File()] = None,
                               service : RestaurantService = Depends(get_restaurant_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, payload=payload)
    await verify_csrf(request)
    restaurant_id = payload.get("restaurant_id")
    parsed_working_hours = None
    if working_hours:
        try:
            parsed_working_hours = json.loads(working_hours)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid working_hours format")
    data = UpdateRestaurantDTO(
        restaurant_name=restaurant_name,
        slug=slug,
        slogan=slogan,
        tagline=tagline,
        short_description=short_description,
        description=description,
        about_title=about_title,
        country=country,
        city=city,
        address=address,
        timezone=timezone,
        currency=currency,
        phone=phone,
        email=email,
        instagram_url=instagram_url,
        working_hours=parsed_working_hours,
        accepts_reservations=accepts_reservations,
        accepts_delivery=accepts_delivery,
        accepts_orders_on_site=accepts_orders_on_site,
        remove_photo=remove_photo)
    updated_restaurant = await service.update_restaurant(restaurant_id, data, photo)
    return {"photo_url": updated_restaurant.photo_url, "success": True}


@router.get("/restaurants/connect/onboarding")
async def start_connect_onboarding(request: Request, service: RestaurantService = Depends(get_restaurant_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await service.get_restaurant_by_id(restaurant_id)
    if not restaurant.stripe_account_id:
        account = stripe.Account.create(
            type="express",
            email=restaurant.email,
            capabilities={
                "transfers": {"requested": True},
                "card_payments": {"requested": True},
            },
            business_profile={"name": restaurant.restaurant_name},
            tos_acceptance={"service_agreement": "full"},
            metadata={"restaurant_id": str(restaurant.id)})
        restaurant.stripe_account_id = account.id
        await service.save(restaurant)
    link = stripe.AccountLink.create(
        account=restaurant.stripe_account_id,
        refresh_url=f"{settings.BASE_URL}/restaurants/connect/refresh?restaurant_id={restaurant.id}",
        return_url=f"{settings.BASE_URL}/restaurants/connect/return?restaurant_id={restaurant.id}",
        type="account_onboarding")
    return RedirectResponse(link.url)

@router.get("/restaurants/connect/refresh")
async def refresh_connect_onboarding(restaurant_id: str, service: RestaurantService = Depends(get_restaurant_dependency)):
    try:
        restaurant_uuid = uuid.UUID(restaurant_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid restaurant_id")
    restaurant = await service.get_restaurant_by_id(restaurant_uuid)
    if not restaurant.stripe_account_id:
        return RedirectResponse("/restaurants/connect/onboarding")
    link = stripe.AccountLink.create(
        account=restaurant.stripe_account_id,
        refresh_url=f"{settings.BASE_URL}/restaurants/connect/refresh?restaurant_id={restaurant.id}",
        return_url=f"{settings.BASE_URL}/restaurants/connect/return?restaurant_id={restaurant.id}",
        type="account_onboarding")
    return RedirectResponse(link.url)

@router.get("/restaurants/connect/return")
async def return_from_connect_onboarding(restaurant_id: str, service: RestaurantService = Depends(get_restaurant_dependency)):
    try:
        restaurant_uuid = uuid.UUID(restaurant_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid restaurant_id")
    restaurant = await service.get_restaurant_by_id(restaurant_uuid)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.stripe_account_id:
        account = stripe.Account.retrieve(restaurant.stripe_account_id)
        restaurant.stripe_charges_enabled = account.charges_enabled
        restaurant.stripe_payouts_enabled = account.payouts_enabled
        await service.save(restaurant)
    return RedirectResponse("/restaurants/add_bank_acc/success")

@router.get("/restaurants/add_bank_acc/success")
async def add_bank_acc_success_page(request : Request):
    return templates.TemplateResponse("add_bank_acc_success.html", {"request" : request})

@router.get("/restaurants/connect/dashboard")
async def connect_dashboard(request: Request, service: RestaurantService = Depends(get_restaurant_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await service.get_restaurant_by_id(restaurant_id)
    if not restaurant.stripe_account_id:
        raise HTTPException(status_code=400, detail="Stripe account not created")
    login_link = stripe.Account.create_login_link(restaurant.stripe_account_id)
    return RedirectResponse(login_link.url)

@router.patch("/restaurants/save_restaurant_webhook")
async def save_restaurant_webhook(restaurant_id : UUID,
                                  stripe_payouts_enabled : bool,
                                  stripe_charges_enabled : bool,
                                  internal_token: str = Header(..., alias="internal_token"),
                                  service: RestaurantService = Depends(get_restaurant_dependency)):
    await verify_internal_token(internal_token)
    restaurant = await service.get_restaurant_by_id(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    restaurant.stripe_charges_enabled = stripe_charges_enabled
    restaurant.stripe_payouts_enabled = stripe_payouts_enabled
    await service.save(restaurant)