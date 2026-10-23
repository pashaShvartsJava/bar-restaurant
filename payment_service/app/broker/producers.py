import json
from uuid import UUID
import aio_pika
from .instance import rabbitmq


async def publish_payment_paid(payment_id: int, client_id: UUID, event_id : UUID, order_id : int):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "payment_paid",
            "payment_id": payment_id,
            "client_id": str(client_id),
            "order_id" : str(order_id)})
        .encode(), message_id=str(event_id), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="payment_paid")

async def publish_subscription_event(subscription_id : str,
                                     restaurant_id : str,
                                     client_id : str,
                                     status : str,
                                     event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "subscription_status_changed",
            "subscription_id": subscription_id,
            "client_id": client_id,
            "restaurant_id": restaurant_id,
            "status": status})
        .encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json")
    await rabbitmq.subscription_exchange.publish(message, routing_key="subscription_routing_key")