from app.repositories.order_item_repository import OrderItemRepository
from app.services.order_service import OrderService
from app.repositories.product_repository import ProductRepository
from app.services.inventory_service import InventoryService
from app.repositories.order_repository import OrderRepository
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.order import OrderCreate
from app.schemas.order import OrderStatus

from sqlalchemy.orm import Session

class OrderApplicationService:
    def __init__(self,db:Session):
        self.db = db
        inventory_repository = InventoryRepository(db)
        product_repository = ProductRepository(db)
        inventory_service = InventoryService(
            inventory_repository,
            product_repository
        )
        order_item_repository = OrderItemRepository(db)
        order_repository = OrderRepository(db)

        self.order_service = OrderService(
            db,
            order_repository,
            order_item_repository,
            product_repository,
            inventory_service
        )

    def create_order(
            self,
            user_id:int,
            data:OrderCreate
    ):
        with self.db.begin():
            return self.order_service.create_order(
                user_id,
                data
            )

    def update_status(
            self,
            order_id:int,
            new_status:OrderStatus
    ):
        with self.db.begin():
            return self.order_service.update_status(
                order_id,
                new_status
            )