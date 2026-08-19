import asyncio
from collections.abc import Awaitable, Callable

from app.db.session import SessionLocal
from app.repositories.outbox_repository import OutboxRepository
from app.messaging.rabbitmq import RabbitMQ
from app.messaging.publisher import EventPublisher


async def publish_pending_events(
    publisher: EventPublisher,
    session_factory: Callable = SessionLocal,
    batch_size: int = 100,
) -> int:
    db = session_factory()

    try:
        repository = OutboxRepository(db)
        events = repository.get_unpublished(limit=batch_size)

        for event in events:
            await publisher.publish(event)
            repository.mark_published(event)

        db.commit()
        return len(events)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def process_events(
    interval_seconds: float = 2,
    publisher_factory: Callable[[RabbitMQ], EventPublisher] = lambda rabbitmq: EventPublisher(
        rabbitmq.exchange
    ),
):

    rabbitmq = RabbitMQ()

    await rabbitmq.connect()

    publisher = publisher_factory(rabbitmq)

    try:

        while True:

            try:
                await publish_pending_events(publisher)

            except Exception as e:

                print(
                    f"Outbox worker error: {e}"
                )

                db.rollback()

            await asyncio.sleep(interval_seconds)

    finally:

        await rabbitmq.close()


if __name__ == "__main__":
    asyncio.run(
        process_events()
    )