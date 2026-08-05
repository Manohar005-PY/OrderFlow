import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.models.enums import UserRole
from app.models.order import Order
from app.models.payment import Payment
from app.models.payment_enums import PaymentProvider, PaymentStatus
from app.core.security import hash_password


def setup_db():
    Base.metadata.create_all(bind=engine)


def test_payments_webhook_idempotent():
    setup_db()

    client = TestClient(app)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "pay@test.com").first()
        if not user:
            user = User(
                email="pay@test.com",
                hashed_password=hash_password("testpass123"),
                full_name="Pay Tester",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        order = db.query(Order).filter(Order.user_id == user.id).first()
        if not order:
            order = Order(user_id=user.id, total_amount=Decimal("100.00"))
            db.add(order)
            db.commit()
            db.refresh(order)
        else:
            order.total_amount = Decimal("100.00")
            db.commit()
            db.refresh(order)

        provider_payment_id = str(uuid.uuid4())

        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if not payment:
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                provider=PaymentProvider.MOCK,
                provider_payment_id=provider_payment_id,
                status=PaymentStatus.PENDING,
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
        else:
            payment.provider_payment_id = provider_payment_id
            payment.status = PaymentStatus.PENDING
            db.commit()
            db.refresh(payment)
    finally:
        db.close()

    # First webhook call
    resp = client.post("/payments/webhook", json={"provider_payment_id": provider_payment_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"

    # Verify order is PAID
    db = SessionLocal()
    try:
        ord = db.query(Order).filter(Order.id == order.id).first()
        assert ord.status == "PAID"
    finally:
        db.close()

    # Second webhook call (idempotency)
    resp2 = client.post("/payments/webhook", json={"provider_payment_id": provider_payment_id})
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["status"] == "SUCCESS"
