from fastapi import APIRouter, Request, HTTPException
from fastapi.params import Depends
from starlette.templating import Jinja2Templates

from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_role
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_conversation_service_dependency, get_restaurant_dependency
from ..service.conversation_service import ConversationService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/r/{slug}/support/user")
async def show_chat(request : Request,
                    slug : str,
                    conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload  = get_payload(request)
    required_role(IdentityRole.USER, payload=payload)
    restaurant = await get_restaurant_dependency(slug)
    conversation = await conversation_service.get_or_create_conversation(payload["sub"], restaurant.id)
    return templates.TemplateResponse("chat_page.html", {"request" : request, "conversation" : conversation})
