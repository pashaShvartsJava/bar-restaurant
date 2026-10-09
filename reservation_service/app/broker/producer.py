import json
from datetime import datetime

from .instance import rabbitmq

import aio_pika


async def publish_reservation_guest(name : str, surname : str, email : str, reservation_start : datetime, event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "change_status",
            "name": name,
            "surname": surname,
            "reservation_start" : reservation_start,
            "email": email})
        .encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="create_reservation")