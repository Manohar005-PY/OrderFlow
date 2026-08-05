import os
import uuid
from decimal import Decimal

# Use a local SQLite DB for the test to avoid needing Postgres
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_run.db"
os.environ["JWT_SECRET_KEY"] = "testsecret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.user import User
from app.models.enums import UserRole
from app.models.order import Order
from app.models.payment import Payment
from app.models.payment_enums import PaymentProvider, PaymentStatus
from app.core.security import hash_password


def setup_db():
    Base.metadata.create_all(bind=engine)


def create_entities():
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

        return provider_payment_id, order.id
    finally:
        db.close()


def print_payment_and_order(order_id, provider_payment_id):
    db = SessionLocal()
    try:
        p = db.query(Payment).filter(Payment.provider_payment_id == provider_payment_id).first()
        o = db.query(Order).filter(Order.id == order_id).first()
        print("DB Payment:", {"id": p.id, "status": p.status, "provider_payment_id": p.provider_payment_id})
        print("DB Order:", {"id": o.id, "status": o.status})
    finally:
        db.close()


def run():
    setup_db()
    provider_payment_id, order_id = create_entities()

    client = TestClient(app)

    print("Before webhook:")
    print_payment_and_order(order_id, provider_payment_id)

    resp = client.post("/payments/webhook", json={"provider_payment_id": provider_payment_id})
    print("First webhook response status:", resp.status_code)
    print("First webhook response body:", resp.json())

    print("After first webhook:")
    print_payment_and_order(order_id, provider_payment_id)

    resp2 = client.post("/payments/webhook", json={"provider_payment_id": provider_payment_id})
    print("Second webhook response status:", resp2.status_code)
    print("Second webhook response body:", resp2.json())

    print("After second webhook:")
    print_payment_and_order(order_id, provider_payment_id)


if __name__ == "__main__":
    run()
