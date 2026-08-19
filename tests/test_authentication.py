import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.models.enums import UserRole
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.core.config import settings


def registration_payload(email):
    return {
        "email": email,
        "password": "testpass123",
        "fullname": "Registration User",
    }


def test_registration_and_duplicate_email(client):
    email = f"register-{uuid.uuid4()}@example.com"

    first = client.post("/auth/register", json=registration_payload(email))
    assert first.status_code == 201
    assert first.json()["email"] == email

    duplicate = client.post("/auth/register", json=registration_payload(email))
    assert duplicate.status_code == 409


def test_login_success_and_invalid_password(client):
    email = f"login-{uuid.uuid4()}@example.com"
    assert client.post("/auth/register", json=registration_payload(email)).status_code == 201

    valid = client.post(
        "/auth/login",
        data={"username": email, "password": "testpass123"},
    )
    assert valid.status_code == 200
    assert valid.json()["token_type"] == "bearer"

    invalid = client.post(
        "/auth/login",
        data={"username": email, "password": "wrong-password"},
    )
    assert invalid.status_code == 401


def test_invalid_token_and_inactive_user_are_rejected(client, db_session):
    invalid = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert invalid.status_code == 401

    inactive = User(
        email=f"inactive-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Inactive User",
        role=UserRole.CUSTOMER,
        is_active=False,
    )
    db_session.add(inactive)
    db_session.commit()

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {create_access_token(str(inactive.id))}"},
    )
    assert response.status_code == 403


def test_expired_token_is_rejected(client):
    token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_customer_cannot_create_product(client, db_session):
    user = User(
        email=f"customer-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Customer User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/products",
        json={
            "sku": f"NOAUTH-{uuid.uuid4().hex[:8]}",
            "name": "Restricted Product",
            "description": "Should not be created",
            "price": "10.00",
            "category": "Test",
        },
        headers={"Authorization": f"Bearer {create_access_token(str(user.id))}"},
    )
    assert response.status_code == 403
