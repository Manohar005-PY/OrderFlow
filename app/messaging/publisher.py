import json

import aio_pika

from app.models.outbox import OutboxEvent


class EventPublisher:

    def __init__(
        self,
        channel: aio_pika.abc.AbstractChannel,
    ):
        self.channel = channel

    async def publish(
        self,
        event: OutboxEvent,
    ):

        message = aio_pika.Message(
            body=event.payload.encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={
                "event_type": event.event_type,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
            },
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key=event.event_type,
        )