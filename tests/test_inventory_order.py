import uuid
from decimal import Decimal

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.user import User


def admin_headers(db):
    user = User(
        email=f"inventory-admin-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Inventory Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def customer_headers(db):
    user = User(
        email=f"order-user-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Order User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def create_product(client, headers, price="19.99"):
    response = client.post(
        "/products",
        json={
            "sku": f"INV-{uuid.uuid4().hex[:10]}",
            "name": "Inventory Product",
            "description": "Product for inventory tests",
            "price": price,
            "category": "Testing",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_inventory(client, headers, product_id, quantity=10):
    response = client.post(
        "/inventory",
        json={"product_id": product_id, "quantity": quantity},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_inventory_stock_reservation_release_and_invariants(client, db_session):
    headers = admin_headers(db_session)
    product = create_product(client, headers)
    inventory = create_inventory(client, headers, product["id"], quantity=10)
    assert inventory["quantity"] - inventory["reserved_quantity"] == 10

    added = client.post(
        f"/inventory/{product['id']}/add-stock",
        json={"quantity": 5},
        headers=headers,
    )
    assert added.status_code == 200
    assert added.json()["quantity"] == 15

    removed = client.post(
        f"/inventory/{product['id']}/remove-stock",
        json={"quantity": 3},
        headers=headers,
    )
    assert removed.status_code == 200
    assert removed.json()["quantity"] == 12

    reserved = client.post(
        f"/inventory/{product['id']}/reserve-stock",
        json={"quantity": 8},
        headers=headers,
    )
    assert reserved.status_code == 200
    assert reserved.json()["reserved_quantity"] == 8
    assert reserved.json()["quantity"] - reserved.json()["reserved_quantity"] == 4

    too_much = client.post(
        f"/inventory/{product['id']}/reserve-stock",
        json={"quantity": 5},
        headers=headers,
    )
    assert too_much.status_code == 400

    released = client.post(
        f"/inventory/{product['id']}/release-stock",
        json={"quantity": 3},
        headers=headers,
    )
    assert released.status_code == 200
    assert released.json()["reserved_quantity"] == 5

    over_release = client.post(
        f"/inventory/{product['id']}/release-stock",
        json={"quantity": 6},
        headers=headers,
    )
    assert over_release.status_code == 400


def test_duplicate_inventory_is_rejected(client, db_session):
    headers = admin_headers(db_session)
    product = create_product(client, headers)
    create_inventory(client, headers, product["id"])

    duplicate = client.post(
        "/inventory",
        json={"product_id": product["id"], "quantity": 10},
        headers=headers,
    )
    assert duplicate.status_code in (400, 409)


def test_order_reserves_stock_uses_database_price_and_rejects_duplicates(
    client,
    db_session,
):
    admin = admin_headers(db_session)
    product = create_product(client, admin, price="23.45")
    create_inventory(client, admin, product["id"], quantity=10)
    customer = customer_headers(db_session)

    order = client.post(
        "/order",
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
        headers=customer,
    )
    assert order.status_code == 201
    body = order.json()
    assert Decimal(body["total_amount"]) == Decimal("46.90")
    assert body["items"][0]["unit_price"] == "23.45"

    db_session.expire_all()
    inventory = db_session.query(Inventory).filter_by(product_id=product["id"]).one()
    assert inventory.reserved_quantity == 2
    assert inventory.available_quantity == 8

    duplicate = client.post(
        "/order",
        json={
            "items": [
                {"product_id": product["id"], "quantity": 1},
                {"product_id": product["id"], "quantity": 1},
            ]
        },
        headers=customer,
    )
    assert duplicate.status_code == 400


def test_order_rejects_missing_product_and_insufficient_inventory(client, db_session):
    admin = admin_headers(db_session)
    product = create_product(client, admin)
    create_inventory(client, admin, product["id"], quantity=1)
    customer = customer_headers(db_session)

    missing = client.post(
        "/order",
        json={"items": [{"product_id": 999999999, "quantity": 1}]},
        headers=customer,
    )
    assert missing.status_code == 404

    insufficient = client.post(
        "/order",
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
        headers=customer,
    )
    assert insufficient.status_code == 400
