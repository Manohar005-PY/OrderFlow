import asyncio
import json
from types import SimpleNamespace

from app.workers import payment_consumer
from app.workers.payment_consumer import handle_payment_message


class FakeExchange:
    def __init__(self):
        self.messages = []

    async def publish(self, message, routing_key):
        self.messages.append((message, routing_key))


class FakeMessage:
    def __init__(self, retry_count=0):
        self.message_id = "retry-event"
        self.headers = {
            "event_id": "retry-event",
            "event_type": "PaymentSucceeded",
            "x-retry-count": retry_count,
        }
        self.body = json.dumps({"payment_id": 1}).encode()
        self.content_type = "application/json"
        self.acks = 0
        self.rejects = []

    async def ack(self):
        self.acks += 1

    async def reject(self, requeue):
        self.rejects.append(requeue)


class FakeRabbit:
    def __init__(self):
        self.retry_exchange = FakeExchange()
        self.dlq_exchange = FakeExchange()


def test_failed_message_is_republished_for_retry(monkeypatch):
    async def fail_processing(**kwargs):
        raise RuntimeError("transient failure")

    monkeypatch.setattr(payment_consumer, "process_message", fail_processing)
    message = FakeMessage(retry_count=1)
    rabbit = FakeRabbit()

    asyncio.run(handle_payment_message(message, rabbit))

    assert message.acks == 1
    assert message.rejects == []
    assert len(rabbit.retry_exchange.messages) == 1
    retry_message, routing_key = rabbit.retry_exchange.messages[0]
    assert routing_key == "PaymentSucceeded"
    assert retry_message.headers["x-retry-count"] == 2
    assert rabbit.dlq_exchange.messages == []


def test_exhausted_message_is_sent_to_dlq(monkeypatch):
    async def fail_processing(**kwargs):
        raise RuntimeError("permanent failure")

    monkeypatch.setattr(payment_consumer, "process_message", fail_processing)
    message = FakeMessage(retry_count=payment_consumer.MAX_RETRIES)
    rabbit = FakeRabbit()

    asyncio.run(handle_payment_message(message, rabbit))

    assert message.acks == 1
    assert message.rejects == []
    assert rabbit.retry_exchange.messages == []
    assert len(rabbit.dlq_exchange.messages) == 1
