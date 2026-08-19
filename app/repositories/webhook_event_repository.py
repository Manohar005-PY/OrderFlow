from sqlalchemy.orm import Session

from app.models.webhook_event import WebhookEvent


class WebhookEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, provider: str, event_id: str) -> WebhookEvent | None:
        return (
            self.db.query(WebhookEvent)
            .filter(
                WebhookEvent.provider == provider,
                WebhookEvent.event_id == event_id,
            )
            .first()
        )

    def create(self, provider: str, event_id: str) -> WebhookEvent:
        event = WebhookEvent(provider=provider, event_id=event_id)
        self.db.add(event)
        self.db.flush()
        return event
