import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from ..dependencies.dependencies import get_message_service_dependency, get_conversation_service_dependency
from ..service.conversation_service import ConversationService
from ..service.message_service import MessageService
from ..security.jwt.jwt import decode_access_token
from ..security.authorization.authorization import required_role
from ..security.role.role import IdentityRole
from ..chat_manager.manager import ChatManager

router = APIRouter()

chat_manager = ChatManager()

@router.websocket("/ws/support/{conversation_id}")
async def support_websocket(websocket: WebSocket, conversation_id: int,
                            message_service : MessageService = Depends(get_message_service_dependency),
                            conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    token = websocket.cookies.get("access_token")
    if token is None:
        await websocket.close(code=1008)
        return
    payload = decode_access_token(token)
    required_role(IdentityRole.USER, payload=payload)
    await chat_manager.connect(conversation_id=conversation_id, websocket=websocket)
    sender_id = payload["sub"]
    sender_role = payload["role"]
    try:
        while True:
            text = await websocket.receive_text()

            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                event = None
            if event and event.get("type") == "read":
                message_id = event["message_id"]
                await conversation_service.mark_as_read_by_user(conversation_id=conversation_id, message_id=message_id)
                continue

            message = await message_service.create_message(conversation_id, sender_id, sender_role, text)
            message_data = {
                "id" : message.id,
                "conversation_id": conversation_id,
                "sender_id": sender_id,
                "sender_role": sender_role,
                "text": message.text,
                "created_at": message.created_at.isoformat()
            }
            await chat_manager.send_to_conversation(conversation_id=conversation_id, data=message_data)
    except WebSocketDisconnect:
        await chat_manager.disconnect(conversation_id=conversation_id, websocket=websocket)