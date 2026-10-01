import json
from decimal import Decimal
from uuid import UUID
from .instance import rabbitmq

import aio_pika

from ..models.orders import OrderStatus


async def publish_change_status(client_id : str,
                                order_number : str,
                                order_status : str,
                                email : str,
                                order_items : list,
                                sum : str,
                                event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "change_status",
            "client_id": client_id,
            "order_number": order_number,
            "order_status": order_status,
            "order_items" : order_items,
            "sum" : sum,
            "email": email})
        .encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="change_status_event")