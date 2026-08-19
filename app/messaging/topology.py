import aio_pika


EXCHANGE_NAME = "orderflow.events"
PAYMENT_QUEUE = "orderflow.payment.events"
PAYMENT_RETRY_EXCHANGE = "orderflow.payment.retry"
PAYMENT_SUCCEEDED_RETRY_QUEUE = "orderflow.payment.succeeded.retry.queue"
PAYMENT_FAILED_RETRY_QUEUE = "orderflow.payment.failed.retry.queue"
PAYMENT_DLQ_EXCHANGE = "orderflow.payment.dlq"
PAYMENT_DLQ_QUEUE = "orderflow.payment.dlq.queue"
PAYMENT_ROUTING_KEY = "payment-event"


async def setup_topology(channel):

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

    retry_exchange = await channel.declare_exchange(
        PAYMENT_RETRY_EXCHANGE,
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )
    for queue_name, routing_key in (
        (PAYMENT_SUCCEEDED_RETRY_QUEUE, "PaymentSucceeded"),
        (PAYMENT_FAILED_RETRY_QUEUE, "PaymentFailed"),
    ):
        retry_queue = await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-message-ttl": 5000,
                "x-dead-letter-exchange": EXCHANGE_NAME,
                "x-dead-letter-routing-key": routing_key,
            },
        )
        await retry_queue.bind(retry_exchange, routing_key=routing_key)

    dlq_exchange = await channel.declare_exchange(
        PAYMENT_DLQ_EXCHANGE,
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )
    dlq_queue = await channel.declare_queue(
        PAYMENT_DLQ_QUEUE,
        durable=True,
    )
    await dlq_queue.bind(dlq_exchange, routing_key=PAYMENT_ROUTING_KEY)

    return exchange, queue