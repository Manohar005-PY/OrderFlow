import os
from collections import Counter
from threading import Lock

from locust import HttpUser, between, events, task
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.inventory import Inventory
from app.models.payment import Payment

OUTCOMES = Counter()
OUTCOMES_LOCK = Lock()



def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set for this load scenario")
    return value


class InventoryReservationUser(HttpUser):
    wait_time = between(0.01, 0.05)

    def on_start(self):
        self.product_id = int(required("LOAD_PRODUCT_ID"))
        self.quantity = int(os.getenv("LOAD_RESERVATION_QUANTITY", "3"))
        email = required("LOAD_TEST_EMAIL")
        password = required("LOAD_TEST_PASSWORD")

        response = self.client.post(
            "/auth/login",
            data={"username": email, "password": password},
            name="login",
        )
        if response.status_code != 200:
            response.failure(f"login failed: {response.status_code}")
            raise RuntimeError("load-test login failed")
        self.client.headers.update(
            {"Authorization": f"Bearer {response.json()['access_token']}"}
        )

    @task
    def reserve_inventory(self):
        with self.client.post(
            f"/inventory/{self.product_id}/reserve-stock",
            json={"quantity": self.quantity},
            name="reserve-stock",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                outcome = "success"
                response.success()
            elif response.status_code == 400:
                outcome = "insufficient_stock"
                response.success()
            else:
                response.failure(f"unexpected status: {response.status_code}")
                outcome = "unexpected_failure"
            with OUTCOMES_LOCK:
                OUTCOMES[outcome] += 1


class PaymentIdempotencyUser(HttpUser):
    wait_time = between(0.01, 0.05)

    def on_start(self):
        self.order_id = int(required("LOAD_ORDER_ID"))
        self.idempotency_key = required("LOAD_IDEMPOTENCY_KEY")

    @task
    def create_idempotent_payment(self):
        with self.client.post(
            "/payments",
            json={
                "order_id": self.order_id,
                "provider": "MOCK",
                "idempotency_key": self.idempotency_key,
            },
            name="create-payment-same-key",
            catch_response=True,
        ) as response:
            if response.status_code in (201, 409):
                outcome = "resolved" if response.status_code == 201 else "conflict"
                response.success()
            else:
                response.failure(f"unexpected status: {response.status_code}")
                outcome = "unexpected_failure"
            with OUTCOMES_LOCK:
                OUTCOMES[outcome] += 1


class OrderFlowLoadShape(HttpUser):
    abstract = True


def print_inventory_invariant():
    db = SessionLocal()
    try:
        product_id = int(required("LOAD_PRODUCT_ID"))
        inventory = db.query(Inventory).filter_by(product_id=product_id).one()
        print(
            "inventory result: "
            f"quantity={inventory.quantity}, "
            f"reserved={inventory.reserved_quantity}, "
            f"available={inventory.available_quantity}"
        )
        if inventory.reserved_quantity > inventory.quantity:
            raise RuntimeError("inventory invariant violated")
    finally:
        db.close()


def print_payment_idempotency_invariant():
    db = SessionLocal()
    try:
        key = required("LOAD_IDEMPOTENCY_KEY")
        count = (
            db.query(func.count(Payment.id))
            .filter(Payment.idempotency_key == key)
            .scalar()
        )
        print(f"payment result: idempotency_key={key}, rows={count}")
        if count != 1:
            raise RuntimeError("payment idempotency invariant violated")
    finally:
        db.close()


@events.test_stop.add_listener
def verify_load_invariants(environment, **kwargs):
    print(f"load outcomes: {dict(OUTCOMES)}")
    scenario = os.getenv("LOAD_SCENARIO", "")
    try:
        if scenario == "inventory":
            print_inventory_invariant()
        elif scenario == "payment":
            print_payment_idempotency_invariant()
    except Exception as error:
        environment.process_exit_code = 1
        print(f"load invariant failure: {error}")
