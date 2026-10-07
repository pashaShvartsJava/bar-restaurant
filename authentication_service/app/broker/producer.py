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

async def publish_change_password_verification(email : EmailStr, token : str, event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "change_password_verification",
            "email": email,
            "token": token})
        .encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="change_password_verification_event")

async def publish_reset_password(email : EmailStr, token : str, event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "reset_password",
            "email": email,
            "token": token
        }).encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="reset_password_event")