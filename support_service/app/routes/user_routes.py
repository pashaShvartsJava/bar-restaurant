from fastapi import APIRouter, HTTPException
from starlette.templating import Jinja2Templates
from ..security.jwt.jwt import get_payload
from ..security.authorization.authorization import required_role
from ..security.role.role import IdentityRole
from ..dependencies.dependencies import get_conversation_service_dependency, get_restaurant_dependency
from ..service.conversation_service import ConversationService
from uuid import UUID, uuid4
from fastapi import Request, Response, Depends

GUEST_COOKIE_NAME = "guest_id"

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

@router.get("/support/b2c")
async def show_customer_b2c_chat(request: Request,
                                 response: Response,
                                 conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    payload = get_payload(request)
    is_authenticated = bool(payload and payload.get("sub"))
    if is_authenticated:
        required_role(IdentityRole.USER, payload)
        try:
            user_id = UUID(str(payload["sub"]))
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid user ID")
    else:
        guest_id = request.cookies.get(GUEST_COOKIE_NAME)
        try:
            user_id = UUID(guest_id) if guest_id else uuid4()
        except (ValueError, TypeError):
            user_id = uuid4()
        response.set_cookie(
            key=GUEST_COOKIE_NAME,
            value=str(user_id),
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/")
    conversation = await conversation_service.get_or_create_b2c_conversation(user_id)
    return templates.TemplateResponse("b2c_chat.html",
                                      {"request": request,
                                       "conversation": conversation,
                                       "chat_side": "user",
                                       "is_authenticated": is_authenticated})
