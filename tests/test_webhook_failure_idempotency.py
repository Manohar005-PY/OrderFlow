import uuid
from decimal import Decimal

from app.gateway.mock_gateway import MockGateway
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.outbox import OutboxEvent
from app.models.payment import Payment
from app.models.payment_enums import PaymentProvider, PaymentStatus
from app.models.product import Product
from app.models.user import User


def test_failed_webhook_is_idempotent(client, db_session, monkeypatch, signed_webhook):
    user = User(
        email=f"webhook-failure-{uuid.uuid4()}@example.com",
        hashed_password="not-used",
        full_name="Webhook User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    product = Product(
        sku=f"HOOK-{uuid.uuid4().hex[:10]}",
        name="Webhook Product",
        description="Product for webhook tests",
        price=Decimal("5.00"),
        category="Testing",
    )
    db_session.add_all([user, product])
    db_session.flush()
    inventory = Inventory(product_id=product.id, quantity=5, reserved_quantity=1)
    order = Order(user_id=user.id, total_amount=Decimal("5.00"))
    db_session.add_all([inventory, order])
    db_session.flush()
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
        )
    )
    provider_payment_id = f"provider-{uuid.uuid4()}"
    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        provider=PaymentProvider.MOCK,
        provider_payment_id=provider_payment_id,
        status=PaymentStatus.PENDING,
    )
    db_session.add(payment)
    db_session.commit()

    monkeypatch.setattr(MockGateway, "verify_payment", lambda self, provider_id: False)

    payload, headers = signed_webhook(provider_payment_id)
    first = client.post("/payments/webhook", content=payload, headers=headers)
    second = client.post("/payments/webhook", content=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "FAILED"
    assert second.json()["status"] == "FAILED"

    db_session.expire_all()
    assert db_session.get(Inventory, inventory.id).reserved_quantity == 0
    events = (
        db_session.query(OutboxEvent)
        .filter_by(aggregate_id=payment.id, aggregate_type="Payment")
        .all()
    )
    assert [event.event_type for event in events] == ["PaymentFailed"]
