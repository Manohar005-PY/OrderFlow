import aio_pika

from app.core.config import settings
from app.messaging.topology import setup_topology


class RabbitMQ:

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.retry_exchange = None
        self.dlq_exchange = None

    async def connect(self):

        self.connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )

        self.channel = await self.connection.channel()

        await self.channel.set_qos(
            prefetch_count=10
        )

        self.exchange, _ = await setup_topology(
            self.channel
        )
        self.retry_exchange = await self.channel.get_exchange(
            "orderflow.payment.retry"
        )
        self.dlq_exchange = await self.channel.get_exchange(
            "orderflow.payment.dlq"
        )

    async def close(self):

        if self.connection:
            await self.connection.close()