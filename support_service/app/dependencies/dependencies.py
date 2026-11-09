import httpx

from ..repository.conversation_repository import ConversationRepository
from ..schema.restaurant_schema import RestaurantConstructorDTO
from ..service.conversation_service import ConversationService
from ..repository.message_repository import MessageRepository
from ..service.message_service import MessageService
from ..database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.config import settings

INTERNAL_TOKEN=settings.internal_token

client_connection: httpx.AsyncClient | None = None

async def get_client() -> httpx.AsyncClient:
    global client_connection
    if client_connection is None:
        client_connection = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            headers={"internal_token": INTERNAL_TOKEN},
        )
    return client_connection

def get_conversation_service_dependency(db : AsyncSession = Depends(get_db)):
    return ConversationService(ConversationRepository(db))

def get_message_service_dependency(db : AsyncSession = Depends(get_db)):
    return MessageService(MessageRepository(db))

async def get_restaurant_dependency(slug : str):
    client = await get_client()
    response = await client.get(url="http://restaurant-service:8010/restaurants/get_restaurant_by_slug",
                                    headers={"internal_token" : INTERNAL_TOKEN},
                                    params={"slug" : slug})
    return RestaurantConstructorDTO(**response.json())