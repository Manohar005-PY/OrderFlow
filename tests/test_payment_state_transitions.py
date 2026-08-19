import uuid
from decimal import Decimal

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.outbox import OutboxEvent
from app.models.payment import Payment
from app.models.product import Product
from app.models.user import User
from app.gateway.mock_gateway import MockGateway


def create_user(db):
    user = User(
        email=f"state-user-{uuid.uuid4()}@example.com",
        hashed_password="not-used",
        full_name="State User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_payment_success_marks_order_paid_and_creates_outbox(client, db_session):
    order = Order(user_id=create_user(db_session).id, total_amount=Decimal("30.00"))
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    created = client.post(
        "/payments",
        json={
            "order_id": order.id,
            "provider": "MOCK",
            "idempotency_key": f"success-{uuid.uuid4()}",
        },
    )
    assert created.status_code == 201
    payment_id = created.json()["id"]

    confirmed = client.post(f"/payments/{payment_id}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "SUCCESS"

    db_session.expire_all()
    assert db_session.get(Order, order.id).status.value == "PAID"
    events = (
        db_session.query(OutboxEvent)
        .filter_by(aggregate_id=payment_id, aggregate_type="Payment")
        .all()
    )
    assert [event.event_type for event in events] == ["PaymentSucceeded"]
    assert events[0].published_at is None


def test_payment_failure_releases_inventory_cancels_order_and_emits_event(
    client,
    db_session,
    monkeypatch,
):
    user = create_user(db_session)
    product = Product(
        sku=f"PAY-{uuid.uuid4().hex[:10]}",
        name="Payment Product",
        description="Product for payment failure",
        price=Decimal("15.00"),
        category="Testing",
    )
    db_session.add(product)
    db_session.flush()
    inventory = Inventory(product_id=product.id, quantity=5, reserved_quantity=2)
    order = Order(user_id=user.id, total_amount=Decimal("30.00"))
    db_session.add_all([inventory, order])
    db_session.flush()
    db_session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=2, unit_price=product.price))
    db_session.commit()
    db_session.refresh(order)

    created = client.post(
        "/payments",
        json={
            "order_id": order.id,
            "provider": "MOCK",
            "idempotency_key": f"failure-{uuid.uuid4()}",
        },
    )
    payment_id = created.json()["id"]
    monkeypatch.setattr(MockGateway, "verify_payment", lambda self, provider_id: False)

    confirmed = client.post(f"/payments/{payment_id}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "FAILED"

    db_session.expire_all()
    assert db_session.get(Order, order.id).status.value == "CANCELLED"
    assert db_session.get(Inventory, inventory.id).reserved_quantity == 0
    events = (
        db_session.query(OutboxEvent)
        .filter_by(aggregate_id=payment_id, aggregate_type="Payment")
        .all()
    )
    assert [event.event_type for event in events] == ["PaymentFailed"]
