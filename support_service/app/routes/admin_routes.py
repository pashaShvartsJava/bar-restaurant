import uuid
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.params import Depends, Header
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..dependencies.dependencies import get_restaurant_dependency_by_id
from ..schema.susbcription_schema import PlanId
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_conversation_service_dependency, get_restaurant_dependency, \
    get_plan_in_cache, required_plans, verify_restaurant_status
from ..service.conversation_service import ConversationService
from uuid import UUID
from ..config.config import settings

INTERNAL_TOKEN = settings.internal_token
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def verify_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403)

@router.get("/support/admin")
async def show_admin_chat(request : Request,
                    identity_id : UUID,
                    conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload  = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    current_plan_id = await get_plan_in_cache(restaurant_id)
    await required_plans(current_plan_id, PlanId.ONLINE, PlanId.ADVANCED, PlanId.PROFESSIONAL)
    conversation = await conversation_service.get_or_create_admin_conversation(identity_id, UUID(payload["sub"]), restaurant_id)
    return templates.TemplateResponse("admin_chat_page.html", {"request" : request, "conversation" : conversation})

@router.post("/support/admin/{conversation_id}/free_conversation")
async def free_conversation(request : Request,
                            conversation_id : int,
                            conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    await verify_csrf(request)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    current_plan_id = await get_plan_in_cache(restaurant_id)
    await required_plans(current_plan_id, PlanId.ONLINE, PlanId.ADVANCED, PlanId.PROFESSIONAL)
    await conversation_service.free_conversation(conversation_id, restaurant_id)
    return RedirectResponse(url="/admin_panel/all_customers", status_code=303)

@router.get("/support/general_support")
async def general_support(request : Request, conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    restaurant_id = payload.get("restaurant_id")
    restaurant = await get_restaurant_dependency_by_id(restaurant_id)
    await verify_restaurant_status(restaurant.status)
    current_plan_id = await get_plan_in_cache(restaurant_id)
    await required_plans(current_plan_id, PlanId.ONLINE, PlanId.ADVANCED, PlanId.PROFESSIONAL)
    if restaurant.stripe_account_id is None:
        raise HTTPException(detail="Connect your bank account to your account in admin panel via 'Manage account' button at first.", status_code=403)
    conversations = await conversation_service.get_unread_conversations(restaurant_id)
    return templates.TemplateResponse("general_support.html", {"request" : request, "conversations" : conversations})

@router.get("/support/unread/count")
async def get_unread_support_count(restaurant_id : str,
                                   internal_token : str = Header(..., alias="internal_token"),
                                   conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    if internal_token != INTERNAL_TOKEN or internal_token is None:
        raise HTTPException(detail="Forbidden", status_code=403)
    current_plan_id = await get_plan_in_cache(restaurant_id)
    await required_plans(current_plan_id, PlanId.ONLINE, PlanId.ADVANCED, PlanId.PROFESSIONAL)
    count = await conversation_service.count_unread_conversations(uuid.UUID(restaurant_id))
    return {"count": count}

@router.get("/support/admin/b2b/{restaurant_id}")
async def show_b2b_chat(request: Request,
                        restaurant_id: UUID,
                        conversation_id: Optional[int] = None,
                        conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    if conversation_id is not None:
        conversation = await conversation_service.get_conversation_by_id(conversation_id, restaurant_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await conversation_service.get_or_create_fdc_conversation(conversation_id, restaurant_id)
    return templates.TemplateResponse("b2b_chat.html", {"request": request, "conversation": conversation, "chat_side": "restaurant"})
