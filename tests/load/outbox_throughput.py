import argparse
import asyncio
import time
import uuid

from sqlalchemy import func

from app.db.session import SessionLocal
from app.messaging.publisher import EventPublisher
from app.messaging.rabbitmq import RabbitMQ
from app.models.outbox import OutboxEvent
from app.workers.outbox_worker import publish_pending_events


async def run(event_count: int) -> None:
    run_id = uuid.uuid4().hex
    db = SessionLocal()
    events = [
        OutboxEvent(
            event_type="PaymentSucceeded",
            aggregate_type="LoadTest",
            aggregate_id=index,
            payload=(
                '{"load_test_id":"%s","sequence":%d}'
                % (run_id, index)
            ),
        )
        for index in range(event_count)
    ]
    db.add_all(events)
    db.commit()
    event_ids = [event.id for event in events]
    db.close()

    rabbitmq = RabbitMQ()
    await rabbitmq.connect()
    publisher = EventPublisher(rabbitmq.exchange)
    started = time.perf_counter()

    try:
        while True:
            db = SessionLocal()
            try:
                published = (
                    db.query(func.count(OutboxEvent.id))
                    .filter(
                        OutboxEvent.id.in_(event_ids),
                        OutboxEvent.published_at.is_not(None),
                    )
                    .scalar()
                )
            finally:
                db.close()

            if published == event_count:
                break
            await publish_pending_events(publisher, batch_size=100)
    finally:
        await rabbitmq.close()

    elapsed = time.perf_counter() - started
    db = SessionLocal()
    try:
        published = (
            db.query(func.count(OutboxEvent.id))
            .filter(
                OutboxEvent.id.in_(event_ids),
                OutboxEvent.published_at.is_not(None),
            )
            .scalar()
        )
        pending = event_count - published
    finally:
        db.close()

    print(
        f"created={event_count} published={published} pending={pending} "
        f"elapsed_seconds={elapsed:.3f} events_per_second={published / elapsed:.2f}"
    )
    if published + pending != event_count or pending != 0:
        raise RuntimeError("outbox throughput invariant failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(run(args.events))
