import json
from collections.abc import Callable

from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.repositories.processed_event_repository import ProcessedEventRepository


def get_event_id(message: AbstractIncomingMessage) -> str:
    event_id = message.headers.get("event_id") if message.headers else None
    if event_id is not None:
        return str(event_id)
    if message.message_id:
        return message.message_id
    raise ValueError("Event message is missing an event ID")


async def process_message(
    message: AbstractIncomingMessage,
    consumer_name: str,
    handler: Callable[[dict, str], None],
    session_factory=SessionLocal,
) -> bool:
    event_id = get_event_id(message)
    event_type = str(message.headers.get("event_type", ""))
    payload = json.loads(message.body)
    db = session_factory()

    try:
        repository = ProcessedEventRepository(db)
        try:
            repository.add(event_id, consumer_name)
            db.flush()
        except IntegrityError:
            db.rollback()
            return False

        handler(payload, event_type)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()