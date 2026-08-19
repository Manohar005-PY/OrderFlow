import uuid
from decimal import Decimal

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User


def create_order(db):
    user = User(
        email=f"payment-user-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Payment User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.flush()
    order = Order(user_id=user.id, total_amount=Decimal("42.00"))
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def test_payment_creation_is_idempotent(client, db_session):
    first_order = create_order(db_session)
    second_order = create_order(db_session)
    key = f"payment-{uuid.uuid4()}"
    payload = {
        "order_id": first_order.id,
        "provider": "MOCK",
        "idempotency_key": key,
    }

    first = client.post("/payments", json=payload)
    assert first.status_code == 201

    retry = client.post("/payments", json=payload)
    assert retry.status_code == 201
    assert retry.json()["id"] == first.json()["id"]

    payments = db_session.query(Payment).filter(Payment.idempotency_key == key).all()
    assert len(payments) == 1

    conflicting = client.post(
        "/payments",
        json={**payload, "order_id": second_order.id},
    )
    assert conflicting.status_code == 409


def test_payment_creation_requires_existing_order(client):
    response = client.post(
        "/payments",
        json={
            "order_id": 999999999,
            "provider": "MOCK",
            "idempotency_key": f"missing-{uuid.uuid4()}",
        },
    )
    assert response.status_code == 404
