from sqlalchemy.orm import Session

from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.services.inventory_service import InventoryService
from app.schemas.inventory import InventoryCreate


class InventoryApplicationService:

    def __init__(
            self,
            db:Session
    ):
        self.db = db

        inventory_repository = InventoryRepository(db)
        product_repository = ProductRepository(db)

        self.inventory_service = InventoryService(
            inventory_repository,
            product_repository
        )

    def create_inventory(
            self,
            data:InventoryCreate
    ):
        with self.db.begin():
            return self.inventory_service.create_inventory(data)

    def add_stock(
            self,
            product_id:int,
            quantity:int,
    ):
        with self.db.begin():
            return self.inventory_service.add_stock(
                product_id,
                quantity,
            )

    def remove_stock(
            self,
            product_id:int,
            quantity:int,
    ):
        with self.db.begin():
            return self.inventory_service.remove_stock(
                product_id,
                quantity
            )

    def reserve_stock(
            self,
            product_id:int,
            quantity:int,
    ):
        with self.db.begin():
            return self.inventory_service.reserve_stock(
                product_id,
                quantity,
            )
    def release_stock(
            self,
            product_id:int,
            quantity:int,
    ):
        with self.db.begin():
            return self.inventory_service.release_stock(
                product_id,
                quantity
            )