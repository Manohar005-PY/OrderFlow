from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.outbox import OutboxEvent


class OutboxRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        event: OutboxEvent,
    ) -> OutboxEvent:

        self.db.add(event)
        self.db.flush()
        self.db.refresh(event)

        return event

    def get_unpublished(
        self,
        limit: int = 100,
    ) -> list[OutboxEvent]:

        return (
            self.db.query(OutboxEvent)
            .filter(
                OutboxEvent.published_at.is_(None)
            )
            .order_by(
                OutboxEvent.created_at
            )
            .limit(limit)
            .all()
        )

    def mark_published(
        self,
        event: OutboxEvent,
    ) -> OutboxEvent:

        event.published_at = datetime.now(timezone.utc)

        self.db.flush()
        self.db.refresh(event)

        return event