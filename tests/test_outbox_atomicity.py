import uuid
from decimal import Decimal

import pytest

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.order import Order
from app.models.outbox import OutboxEvent
from app.models.payment import Payment
from app.models.user import User


def create_order(db):
    user = User(
        email=f"outbox-{uuid.uuid4()}@example.com",
        hashed_password="not-used",
        full_name="Outbox User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.flush()
    order = Order(user_id=user.id, total_amount=Decimal("10.00"))
    db.add(order)
    db.flush()
    return order


def test_payment_order_and_outbox_roll_back_together(db_session):
    order_id = None
    payment_id = None

    with pytest.raises(RuntimeError):
        with db_session.begin():
            order = create_order(db_session)
            order_id = order.id
            payment = Payment(order_id=order.id, amount=order.total_amount, provider="MOCK")
            db_session.add(payment)
            db_session.flush()
            payment_id = payment.id
            db_session.add(
                OutboxEvent(
                    event_type="PaymentSucceeded",
                    aggregate_type="Payment",
                    aggregate_id=payment.id,
                    payload='{"payment_id": 1}',
                )
            )
            raise RuntimeError("force rollback")

    verification = SessionLocal()
    try:
        assert verification.get(Order, order_id) is None
        assert verification.query(Payment).filter_by(id=payment_id).first() is None
        assert (
            verification.query(OutboxEvent)
            .filter_by(aggregate_id=payment_id, aggregate_type="Payment")
            .first()
            is None
        )
    finally:
        verification.close()


def test_committed_outbox_event_starts_unpublished(db_session):
    order = create_order(db_session)
    payment = Payment(order_id=order.id, amount=order.total_amount, provider="MOCK")
    db_session.add(payment)
    db_session.flush()
    event = OutboxEvent(
        event_type="PaymentSucceeded",
        aggregate_type="Payment",
        aggregate_id=payment.id,
        payload='{"payment_id": 1}',
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.published_at is None
