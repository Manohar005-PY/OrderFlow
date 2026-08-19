import asyncio
import logging

import aio_pika

from app.messaging.consumer import process_message
from app.messaging.rabbitmq import RabbitMQ
from app.messaging.topology import PAYMENT_QUEUE


logger = logging.getLogger(__name__)
CONSUMER_NAME = "payment-events"
MAX_RETRIES = 3


def handle_payment_event(payload: dict, event_type: str) -> None:
    logger.info(
        "Processed payment event",
        extra={
            "event_type": event_type,
            "payment_id": payload.get("payment_id"),
            "order_id": payload.get("order_id"),
        },
    )


def retry_count(message) -> int:
    return int((message.headers or {}).get("x-retry-count", 0))


def copy_message(message, retry: int) -> aio_pika.Message:
    headers = dict(message.headers or {})
    headers["x-retry-count"] = retry
    return aio_pika.Message(
        body=message.body,
        content_type=message.content_type,
        message_id=message.message_id,
        headers=headers,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )


async def consume_payment_events():
    rabbitmq = RabbitMQ()
    await rabbitmq.connect()

    try:
        queue = await rabbitmq.channel.declare_queue(
            PAYMENT_QUEUE,
            durable=True,
        )
        await queue.consume(
            lambda message: handle_payment_message(message, rabbitmq),
            no_ack=False,
        )
        await asyncio.Future()
    finally:
        await rabbitmq.close()


async def handle_payment_message(message, rabbitmq):
    try:
        await process_message(
            message=message,
            consumer_name=CONSUMER_NAME,
            handler=handle_payment_event,
        )
        await message.ack()
    except Exception:
        current_retry = retry_count(message)
        try:
            if current_retry >= MAX_RETRIES:
                await rabbitmq.dlq_exchange.publish(
                    copy_message(message, current_retry),
                    routing_key="payment-event",
                )
            else:
                await rabbitmq.retry_exchange.publish(
                    copy_message(message, current_retry + 1),
                    routing_key=message.headers["event_type"],
                )
            await message.ack()
        except Exception:
            await message.reject(requeue=True)
            raise
        logger.exception("Payment event processing failed")


if __name__ == "__main__":
    asyncio.run(consume_payment_events())