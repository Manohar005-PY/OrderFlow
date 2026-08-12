import asyncio

from app.db.session import SessionLocal
from app.repositories.outbox_repository import OutboxRepository
from app.messaging.rabbitmq import RabbitMQ
from app.messaging.publisher import EventPublisher


async def process_events():

    rabbitmq = RabbitMQ()

    await rabbitmq.connect()

    publisher = EventPublisher(
        rabbitmq.channel
    )

    try:
        while True:

            db = SessionLocal()

            try:
                repository = OutboxRepository(db)

                events = repository.get_unpublished()

                for event in events:

                    await publisher.publish(event)

                    repository.mark_published(event)

                db.commit()

            except Exception:
                db.rollback()

            finally:
                db.close()

            await asyncio.sleep(2)

    finally:
        await rabbitmq.close()