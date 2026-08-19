import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from app.core.exception import InsufficentStockException
from app.db.session import SessionLocal
from app.models.inventory import Inventory
from app.models.product import Product
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.services.inventory_service import InventoryService


def test_concurrent_reservations_cannot_oversell(db_session):
    product = Product(
        sku=f"CONC-{uuid.uuid4().hex[:10]}",
        name="Concurrency Product",
        description="Product for locking tests",
        price=Decimal("10.00"),
        category="Testing",
    )
    db_session.add(product)
    db_session.flush()
    inventory = Inventory(product_id=product.id, quantity=10, reserved_quantity=0)
    db_session.add(inventory)
    db_session.commit()
    product_id = product.id

    barrier = threading.Barrier(2)

    def reserve():
        db = SessionLocal()
        try:
            barrier.wait()
            service = InventoryService(
                InventoryRepository(db),
                ProductRepository(db),
            )
            with db.begin():
                service.reserve_stock(product_id, 6)
            return "reserved"
        except InsufficentStockException:
            db.rollback()
            return "rejected"
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: reserve(), range(2)))

    assert sorted(results) == ["rejected", "reserved"]

    db_session.expire_all()
    final_inventory = db_session.query(Inventory).filter_by(product_id=product_id).one()
    assert final_inventory.reserved_quantity == 6
    assert final_inventory.reserved_quantity <= final_inventory.quantity
    assert final_inventory.available_quantity == 4
