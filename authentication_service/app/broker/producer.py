import json
import uuid

from pydantic import EmailStr

from .instance import rabbitmq

import aio_pika


async def publish_email_verification(email : EmailStr, token : str, event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "verification_email",
            "email": email,
            "token": token})
        .encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="email_verification_event")