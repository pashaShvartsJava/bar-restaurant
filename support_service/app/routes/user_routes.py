from fastapi import APIRouter, Request
from fastapi.params import Depends
from starlette.templating import Jinja2Templates

from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_role
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_message_service_dependency, get_conversation_service_dependency
from ..service.conversation_service import ConversationService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/support/user")
async def show_chat(request : Request,
                    conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload  = get_payload(request)
    required_role(IdentityRole.USER, payload=payload)
    conversation = await conversation_service.get_or_create_conversation(payload["sub"])
    return templates.TemplateResponse("chat_page.html", {"request" : request, "conversation" : conversation})
