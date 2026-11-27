
import logging

import httpx
from pydantic import BaseModel
from httpx import HTTPStatusError

from ..config.config import settings


logger = logging.getLogger(__name__)
INTERNAL_TOKEN = settings.internal_token
client_connection: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global client_connection
    if client_connection is None:
        client_connection = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0),
                                              headers={"internal_token": INTERNAL_TOKEN})
    return client_connection


async def send_recipe_data_to_wh_service_dto(list_order_dto: BaseModel, restaurant_id: str, order_number : str):
    client = await get_client()
    try:
        response = await client.post(url="http://warehouse-service:8011/warehouse/check_or_reserve_products_from_warehouse",
                                     json=list_order_dto.model_dump(mode="json"),
                                     params={"restaurant_id": restaurant_id, "order_number" : order_number})
        response.raise_for_status()
        return response
    except HTTPStatusError as exc:
        logger.error("warehouse-service вернул %s: %s", exc.response.status_code, exc.response.text)
        raise
    except httpx.RequestError as exc:
        logger.error("Ошибка соединения с warehouse-service: %s", exc)
        raise
