import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.messaging.consumer import process_message


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def flush(self):
        pass

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class EventConsumerTests(unittest.TestCase):
    def message(self):
        return SimpleNamespace(
            message_id="outbox-1",
            headers={"event_type": "PaymentSucceeded"},
            body=json.dumps({"payment_id": 4, "order_id": 15}).encode(),
        )

    def test_processes_event_once(self):
        session = FakeSession()
        handled = []
        repository = SimpleNamespace(add=lambda event_id, consumer: None)

        with patch(
            "app.messaging.consumer.ProcessedEventRepository",
            return_value=repository,
        ):
            result = asyncio.run(
                process_message(
                    self.message(),
                    "payment-events",
                    lambda payload, event_type: handled.append((payload, event_type)),
                    session_factory=lambda: session,
                )
            )

        self.assertTrue(result)
        self.assertEqual(handled[0][1], "PaymentSucceeded")
        self.assertEqual(handled[0][0]["order_id"], 15)
        self.assertEqual(session.commits, 1)
        self.assertEqual(session.rollbacks, 0)
        self.assertTrue(session.closed)

    def test_handler_failure_rolls_back(self):
        session = FakeSession()
        repository = SimpleNamespace(add=lambda event_id, consumer: None)

        with patch(
            "app.messaging.consumer.ProcessedEventRepository",
            return_value=repository,
        ):
            with self.assertRaisesRegex(RuntimeError, "handler failed"):
                asyncio.run(
                    process_message(
                        self.message(),
                        "payment-events",
                        lambda payload, event_type: (_ for _ in ()).throw(
                            RuntimeError("handler failed")
                        ),
                        session_factory=lambda: session,
                    )
                )

        self.assertEqual(session.commits, 0)
        self.assertEqual(session.rollbacks, 1)
        self.assertTrue(session.closed)


if __name__ == "__main__":
    unittest.main()