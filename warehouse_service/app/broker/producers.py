import json

import aio_pika

from ..broker.instance import rabbitmq


async def publish_add_product_event(name :str,
                                    unit : str,
                                    restaurant_id : str,
                                    product_id  :str,
                                    event_id : str):
    message = aio_pika.Message(
        body=json.dumps({
            "event": "add_product_event",
            "name": name,
            "unit": unit,
            "restaurant_id": restaurant_id,
            "product_id": product_id})
        .encode(), message_id=event_id, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
    await rabbitmq.exchange.publish(message, routing_key="add_product_routing_key")