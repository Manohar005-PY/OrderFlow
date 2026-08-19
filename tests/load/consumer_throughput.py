import argparse
import asyncio
import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from app.db.session import SessionLocal
from app.messaging.consumer import process_message
from app.models.processed_event import ProcessedEvent


def deliver(event_id: str, consumer_name: str, handler) -> bool:
    message = SimpleNamespace(
        message_id=event_id,
        headers={"event_type": "PaymentSucceeded"},
        body=json.dumps({"event_id": event_id}).encode(),
    )
    return asyncio.run(
        process_message(
            message,
            consumer_name,
            handler,
        )
    )


def run(unique_events: int, duplicate_deliveries: int) -> None:
    consumer_name = f"load-consumer-{uuid.uuid4().hex}"
    event_ids = [f"load-event-{uuid.uuid4().hex}" for _ in range(unique_events)]
    deliveries = event_ids + [event_ids[0]] * duplicate_deliveries
    handled = 0
    handled_lock = threading.Lock()

    def handler(payload, event_type):
        nonlocal handled
        with handled_lock:
            handled += 1

    with ThreadPoolExecutor(max_workers=32) as executor:
        results = list(
            executor.map(
                lambda event_id: deliver(event_id, consumer_name, handler),
                deliveries,
            )
        )

    db = SessionLocal()
    try:
        processed = (
            db.query(ProcessedEvent)
            .filter_by(consumer_name=consumer_name)
            .count()
        )
    finally:
        db.close()

    print(
        f"deliveries={len(deliveries)} unique_event_ids={unique_events} "
        f"handler_effects={handled} processed_events={processed} "
        f"first_delivery_results={sum(results)}"
    )
    if handled != unique_events or processed != unique_events:
        raise RuntimeError("consumer idempotency invariant failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--unique-events", type=int, default=1000)
    parser.add_argument("--duplicate-deliveries", type=int, default=1000)
    args = parser.parse_args()
    run(args.unique_events, args.duplicate_deliveries)
