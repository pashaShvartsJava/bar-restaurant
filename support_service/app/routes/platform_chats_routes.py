from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.params import Depends
from starlette.templating import Jinja2Templates

from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..security.authorization.authorization import required_secret_role
from ..dependencies.dependencies import get_restaurant_dependency_by_id, get_restaurants_dependency
from ..security.jwt.jwt import get_payload, get_secret_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_conversation_service_dependency, verify_restaurant_status
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
        raise HTTPException(status_code=403, detail="CSRF protection was triggered.")

@router.get("/support/admin/b2b")
async def show_all_chats_with_b2b_customers(request: Request,
                                            conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_secret_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload)
    restaurants_data = await get_restaurants_dependency()
    restaurants = [RestaurantConstructorDTO.model_validate(item) for item in restaurants_data]
    conversations = await conversation_service.find_b2b_chats()
    conversations_by_restaurant = {}
    for conversation in conversations:
        restaurant_id = str(conversation.restaurant_id)
        existing = conversations_by_restaurant.get(restaurant_id)
        if existing is None or conversation.created_at > existing.created_at:
            conversations_by_restaurant[restaurant_id] = conversation
    restaurant_rows = []
    for restaurant in restaurants:
        conversation = conversations_by_restaurant.get(str(restaurant.id))
        last_message = None
        if conversation and conversation.messages:
            last_message = max(conversation.messages, key=lambda message: message.created_at)
        restaurant_rows.append({"restaurant": restaurant, "conversation": conversation, "last_message": last_message})
    return templates.TemplateResponse("all_b2b_chats.html", {"request": request, "restaurant_rows": restaurant_rows})

@router.get("/support/admin/secret_api/b2b/{restaurant_id}")
async def show_b2b_chat(request: Request,
                        restaurant_id: UUID,
                        conversation_id: Optional[int] = None,
                        conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_secret_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload)
    if conversation_id is not None:
        conversation = await conversation_service.get_conversation_by_id(conversation_id, restaurant_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await conversation_service.get_or_create_fdc_conversation(conversation_id, restaurant_id)
    return templates.TemplateResponse("b2b_chat.html", {"request": request, "conversation": conversation, "chat_side": "admin"})

@router.get("/support/admin/b2c")
async def show_all_chats_with_b2c_customers(request: Request,
                                            conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_secret_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload)
    b2c_chats = await conversation_service.find_b2c_chats()
    return templates.TemplateResponse("all_b2c_chats.html", {"request" : request, "b2c_chats" : b2c_chats})

@router.get("/support/admin/secret_api/b2c/{conversation_id}")
async def show_b2c_chat(request: Request,
                        conversation_id: int,
                        conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_secret_payload(request)
    required_secret_role(IdentityRole.SUPERADMIN, payload)
    conversation = await conversation_service.get_b2c_conversation_by_id(conversation_id)
    return templates.TemplateResponse("b2c_chat.html", {"request": request, "conversation": conversation, "chat_side": "admin"})