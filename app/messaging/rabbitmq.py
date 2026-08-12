import aio_pika

from app.core.config import settings
from app.messaging.topology import setup_topology


class RabbitMQ:

    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )

        self.channel = await self.connection.channel()

        await self.channel.set_qos(
            prefetch_count=10
        )
        await setup_topology(
            self.channel
        )

    async def close(self):
        if self.connection:
            await self.connection.close()