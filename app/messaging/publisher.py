import aio_pika

from app.models.outbox import OutboxEvent


class EventPublisher:

    def __init__(self, exchange):
        self.exchange = exchange

    async def publish(
        self,
        event: OutboxEvent,
    ):

        message = aio_pika.Message(
            body=event.payload.encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event.id),
            headers={
                "event_id": str(event.id),
                "event_type": event.event_type,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
            },
        )

        await self.exchange.publish(
            message,
            routing_key=event.event_type,
        )