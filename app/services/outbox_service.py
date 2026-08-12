from app.repositories.outbox_repository import OutboxRepository

class OutboxService:
    def __init__(
            self,
            outbox_repository:OutboxRepository
    ):
        self.outbox_repository = outbox_repository

    def get_pending_events(self):
        return self.outbox_repository.get_unpublished()