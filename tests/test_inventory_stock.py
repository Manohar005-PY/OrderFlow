import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def make_auth_headers(client: TestClient):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "inventory@test.com").first()
        if not user:
            user = User(
                email="inventory@test.com",
                hashed_password=hash_password("testpass123"),
                full_name="Inventory Tester",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = client.post(
            "/auth/login",
            data={"username": "inventory@test.com", "password": "testpass123"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        ).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def test_add_stock_updates_quantity(client: TestClient):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.sku == "INV-TEST-1").first()
        if not product:
            product = Product(
                sku="INV-TEST-1",
                name="Inventory Test Product",
                description="For stock operation tests",
                price=19.99,
                category="Test",
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
        if not inventory:
            inventory = Inventory(product_id=product.id, quantity=50, reserved_quantity=0)
            db.add(inventory)
            db.commit()
            db.refresh(inventory)
        else:
            inventory.quantity = 50
            inventory.reserved_quantity = 0
            db.commit()
            db.refresh(inventory)
    finally:
        db.close()

    headers = make_auth_headers(client)

    first_response = client.post(
        f"/inventory/{product.id}/add-stock",
        json={"quantity": 20},
        headers=headers,
    )
    assert first_response.status_code == 200
    assert first_response.json()["quantity"] == 70
    assert first_response.json()["reserved_quantity"] == 0

    second_response = client.post(
        f"/inventory/{product.id}/add-stock",
        json={"quantity": 5},
        headers=headers,
    )
    assert second_response.status_code == 200
    assert second_response.json()["quantity"] == 75
    assert second_response.json()["reserved_quantity"] == 0
