import asyncio
import json
import uuid
from types import SimpleNamespace

from app.db.session import SessionLocal
from app.messaging.consumer import process_message
from app.models.processed_event import ProcessedEvent


def test_duplicate_event_is_processed_once():
    event_id = f"consumer-test-event-{uuid.uuid4()}"
    message = SimpleNamespace(
        message_id=event_id,
        headers={"event_type": "PaymentSucceeded"},
        body=json.dumps({"payment_id": 1, "order_id": 1}).encode(),
    )
    handled = []

    first = asyncio.run(
        process_message(
            message,
            "consumer-idempotency-test",
            lambda payload, event_type: handled.append(payload),
        )
    )
    second = asyncio.run(
        process_message(
            message,
            "consumer-idempotency-test",
            lambda payload, event_type: handled.append(payload),
        )
    )

    assert first is True
    assert second is False
    assert len(handled) == 1

    db = SessionLocal()
    try:
        records = (
            db.query(ProcessedEvent)
            .filter_by(
                event_id=event_id,
                consumer_name="consumer-idempotency-test",
            )
            .all()
        )
        assert len(records) == 1
    finally:
        db.close()
