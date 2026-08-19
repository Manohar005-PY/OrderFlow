import uuid
import hashlib
import hmac
import json
import time

import pytest
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_user(db, role=UserRole.CUSTOMER, is_active=True):
    email = f"test-{uuid.uuid4()}@example.com"
    user = User(
        email=email,
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, "testpass123"


def auth_headers(client, email, password):
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def token_headers(user):
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def signed_webhook():
    def create_signed_webhook(provider_payment_id: str, event_id: str | None = None):
        payload = json.dumps(
            {
                "id": event_id or f"evt-{uuid.uuid4()}",
                "data": {"object": {"provider_payment_id": provider_payment_id}},
            },
            separators=(",", ":"),
        ).encode()
        timestamp = str(int(time.time()))
        digest = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            f"{timestamp}.".encode() + payload,
            hashlib.sha256,
        ).hexdigest()
        return payload, {"Stripe-Signature": f"t={timestamp},v1={digest}"}

    return create_signed_webhook
