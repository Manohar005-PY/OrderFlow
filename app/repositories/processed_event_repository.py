from sqlalchemy.orm import Session

from app.models.processed_event import ProcessedEvent


class ProcessedEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, event_id: str, consumer_name: str) -> ProcessedEvent:
        event = ProcessedEvent(
            event_id=event_id,
            consumer_name=consumer_name,
        )
        self.db.add(event)
        self.db.flush()
        return event