import json
import uuid
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from ..dependencies.dependencies import get_message_service_dependency, get_conversation_service_dependency
from ..service.conversation_service import ConversationService
from ..service.message_service import MessageService
from ..security.jwt.jwt import decode_access_token, decode_secret_access_token
from ..security.authorization.authorization import required_roles, required_secret_role
from ..security.role.role import IdentityRole
from .user_websocket import chat_manager

router = APIRouter()


@router.websocket("/ws/support/admin/{conversation_id}")
async def admin_support_websocket(websocket: WebSocket,
                                  conversation_id: int,
                                  message_service : MessageService = Depends(get_message_service_dependency),
                                  conversation_service : ConversationService = Depends(get_conversation_service_dependency)):
    token = websocket.cookies.get("access_token")
    if token is None:
        await websocket.close(code=1008)
        return
    payload = decode_access_token(token)
    required_roles(IdentityRole.OWNER, IdentityRole.ADMIN, IdentityRole.MODERATOR, payload=payload)
    sender_id = payload["sub"]
    sender_role = payload["role"]
    await chat_manager.connect(conversation_id=conversation_id, websocket=websocket)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                event = None
            if event and event.get("type") == "read":
                print("READ EVENT:", event)
                message_id = event["message_id"]
                await conversation_service.mark_as_read_by_admin(conversation_id=conversation_id, message_id=message_id)
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

@router.websocket("/ws/support/admin/secret_api/b2b/{restaurant_id}/{conversation_id}")
async def admin_b2b_websocket(websocket: WebSocket,
                              restaurant_id: UUID,
                              conversation_id: int,
                              message_service: MessageService = Depends(get_message_service_dependency),
                              conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    token = websocket.cookies.get("access_token")
    payload = decode_secret_access_token(token)
    required_secret_role(IdentityRole.SUPERADMIN, payload)
    conversation = await conversation_service.get_conversation_by_id(conversation_id, restaurant_id)
    if conversation is None or not conversation.is_platform_chat:
        await websocket.close(code=1008)
        return
    sender_id = uuid.UUID(payload["sub"])
    sender_role = "superadmin"
    await chat_manager.connect(conversation_id=conversation_id, websocket=websocket)
    try:
        while True:
            text = await websocket.receive_text()
            text = text.strip()
            if not text:
                continue
            message = await message_service.create_message(conversation_id=conversation_id,
                                                           sender_id=sender_id,
                                                           sender_role=sender_role,
                                                           text=text)
            message_data = {
                "type": "message",
                "id": message.id,
                "conversation_id": conversation_id,
                "sender_id": str(sender_id),
                "sender_role": sender_role,
                "text": message.text,
                "created_at": message.created_at.isoformat()
            }
            await chat_manager.send_to_conversation(conversation_id=conversation_id, data=message_data)
    except WebSocketDisconnect:
        await chat_manager.disconnect(conversation_id=conversation_id, websocket=websocket)

@router.websocket("/ws/support/restaurant/b2b/{restaurant_id}/{conversation_id}")
async def restaurant_b2b_websocket(websocket: WebSocket,
                                   restaurant_id: UUID,
                                   conversation_id: int,
                                   message_service: MessageService = Depends(get_message_service_dependency),
                                   conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
    token = websocket.cookies.get("access_token")
    if token is None:
        await websocket.close(code=1008)
        return
    payload = decode_access_token(token)
    required_roles(IdentityRole.OWNER, IdentityRole.MODERATOR, IdentityRole.ADMIN, payload=payload)
    user_restaurant_id = UUID(str(payload["restaurant_id"]))
    if user_restaurant_id != restaurant_id:
        await websocket.close(code=1008)
        return
    conversation = await conversation_service.get_conversation_by_id( conversation_id, restaurant_id)
    if conversation is None or not conversation.is_platform_chat:
        await websocket.close(code=1008)
        return
    sender_id = restaurant_id
    sender_role = payload.get("role")
    await chat_manager.connect(conversation_id=conversation_id, websocket=websocket)
    try:
        while True:
            text = await websocket.receive_text()
            text = text.strip()
            if not text:
                continue
            message = await message_service.create_message(
                conversation_id=conversation_id,
                sender_id=sender_id,
                sender_role=sender_role,
                text=text
            )
            message_data = {
                "type": "message",
                "id": message.id,
                "conversation_id": conversation_id,
                "sender_id": str(sender_id),
                "sender_role": sender_role,
                "text": message.text,
                "created_at": message.created_at.isoformat()
            }
            await chat_manager.send_to_conversation(conversation_id=conversation_id, data=message_data)
    except WebSocketDisconnect:
        await chat_manager.disconnect(conversation_id=conversation_id, websocket=websocket)

@router.websocket("/ws/support/admin/secret_api/b2c/{conversation_id}")
async def b2c_admin_websocket(websocket: WebSocket,
                                  conversation_id: int,
                                  message_service: MessageService = Depends(get_message_service_dependency),
                                  conversation_service: ConversationService = Depends(get_conversation_service_dependency)):
        token = websocket.cookies.get("access_token")
        if token is None:
            await websocket.close(code=1008)
            return
        payload = decode_secret_access_token(token)
        required_secret_role(IdentityRole.SUPERADMIN, payload=payload)
        sender_id = payload["sub"]
        sender_role = "superadmin"
        conversation = await conversation_service.get_b2c_conversation_by_id(conversation_id=conversation_id)
        if conversation is None:
            await websocket.close(code=1008)
            return
        await chat_manager.connect(conversation_id=conversation_id, websocket=websocket)
        try:
            while True:
                text = await websocket.receive_text()
                try:
                    event = json.loads(text)
                except json.JSONDecodeError:
                    event = None
                if event and event.get("type") == "read":
                    message_id = event["message_id"]
                    await conversation_service.mark_as_read_by_admin(conversation_id=conversation_id, message_id=message_id)
                    continue
                message = await message_service.create_message(
                    conversation_id=conversation_id,
                    sender_id=sender_id,
                    sender_role=sender_role,
                    text=text)
                message_data = {
                    "type": "message",
                    "id": message.id,
                    "conversation_id": conversation_id,
                    "sender_id": sender_id,
                    "sender_role": sender_role,
                    "text": message.text,
                    "created_at": message.created_at.isoformat()}
                await chat_manager.send_to_conversation(conversation_id=conversation_id, data=message_data)
        except WebSocketDisconnect:
            await chat_manager.disconnect(conversation_id=conversation_id, websocket=websocket)