from fastapi import APIRouter, Request, Form
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_roles
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_message_service_dependency, get_conversation_service_dependency
from ..service.conversation_service import ConversationService
from uuid import UUID

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/support/admin")
async def show_admin_chat(request : Request,
                    identity_id : UUID,
                    conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload  = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    conversation = await conversation_service.get_or_create_admin_conversation(identity_id, UUID(payload["sub"]))
    return templates.TemplateResponse("admin_chat_page.html", {"request" : request, "conversation" : conversation})

@router.post("/support/admin/{conversation_id}/free_conversation")
async def free_conversation(request : Request,
                            conversation_id : int,
                            conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_payload(request)
    required_roles(IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    await conversation_service.free_conversation(conversation_id)
    return RedirectResponse(url="/admin_panel/all_customers", status_code=303)