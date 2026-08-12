import aio_pika


EXCHANGE_NAME = "orderflow.events"

PAYMENT_QUEUE = "orderflow.payment.events"


async def setup_topology(
    channel: aio_pika.abc.AbstractChannel,
):

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )

    queue = await channel.declare_queue(
        PAYMENT_QUEUE,
        durable=True,
    )

    await queue.bind(
        exchange,
        routing_key="PaymentSucceeded",
    )

    await queue.bind(
        exchange,
        routing_key="PaymentFailed",
    )

    return exchange, queue