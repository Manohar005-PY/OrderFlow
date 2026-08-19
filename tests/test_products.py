import uuid

from app.core.security import create_access_token, hash_password
from app.models.enums import UserRole
from app.models.user import User


def admin_headers(db_session):
    user = User(
        email=f"product-admin-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Product Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def product_payload(sku=None):
    return {
        "sku": sku or f"SKU-{uuid.uuid4().hex[:10]}",
        "name": "Test Product",
        "description": "A product for integration tests",
        "price": "12.50",
        "category": "Testing",
    }


def test_create_duplicate_lookup_and_deactivate_product(client, db_session):
    headers = admin_headers(db_session)
    payload = product_payload()

    created = client.post("/products", json=payload, headers=headers)
    assert created.status_code == 201
    product_id = created.json()["id"]

    duplicate = client.post("/products", json=payload, headers=headers)
    assert duplicate.status_code == 409

    lookup = client.get(f"/products/{product_id}")
    assert lookup.status_code == 200
    assert lookup.json()["sku"] == payload["sku"]

    active_before = client.get("/products")
    assert active_before.status_code == 200
    assert any(item["id"] == product_id for item in active_before.json())

    deactivated = client.delete(f"/products/{product_id}", headers=headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    active_after = client.get("/products")
    assert all(item["id"] != product_id for item in active_after.json())


def test_missing_product_returns_404(client):
    response = client.get("/products/999999999")
    assert response.status_code == 404
