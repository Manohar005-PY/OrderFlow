import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.workers.outbox_worker import publish_pending_events


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakePublisher:
    def __init__(self, error=False):
        self.error = error
        self.published = []

    async def publish(self, event):
        if self.error:
            raise RuntimeError("RabbitMQ unavailable")
        self.published.append(event.id)


class OutboxWorkerTests(unittest.TestCase):
    def test_publishes_and_commits_events(self):
        session = FakeSession()
        publisher = FakePublisher()
        events = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        repository = SimpleNamespace(
            get_unpublished=lambda limit: events,
            mark_published=lambda event: setattr(event, "published", True),
        )

        with patch("app.workers.outbox_worker.OutboxRepository", return_value=repository):
            count = asyncio.run(
                publish_pending_events(publisher, session_factory=lambda: session)
            )

        self.assertEqual(count, 2)
        self.assertEqual(publisher.published, [1, 2])
        self.assertTrue(all(event.published for event in events))
        self.assertEqual(session.commits, 1)
        self.assertEqual(session.rollbacks, 0)
        self.assertTrue(session.closed)

    def test_rolls_back_when_publishing_fails(self):
        session = FakeSession()
        publisher = FakePublisher(error=True)
        event = SimpleNamespace(id=1)
        repository = SimpleNamespace(
            get_unpublished=lambda limit: [event],
            mark_published=lambda current: setattr(current, "published", True),
        )

        with patch("app.workers.outbox_worker.OutboxRepository", return_value=repository):
            with self.assertRaisesRegex(RuntimeError, "RabbitMQ unavailable"):
                asyncio.run(
                    publish_pending_events(publisher, session_factory=lambda: session)
                )

        self.assertFalse(hasattr(event, "published"))
        self.assertEqual(session.commits, 0)
        self.assertEqual(session.rollbacks, 1)
        self.assertTrue(session.closed)


if __name__ == "__main__":
    unittest.main()