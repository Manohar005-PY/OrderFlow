from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_enums import OrderStatus
from app.services.order_state import VALID_TRANSITIONS

from app.repositories.order_repository import OrderRepository
from app.repositories.order_item_repository import OrderItemRepository
from app.repositories.product_repository import ProductRepository
# from app.repositories.inventory_repository import InventoryRepository
from app.services.inventory_service import InventoryService

from app.schemas.order import OrderCreate

from app.core.exception import ProductNotFoundException, DuplicateProductException,OrderNotFoundExceptiion,InvalidOrderStatusTransitionException

class OrderService:

    def __init__(
            self,
            db:Session,
            order_repository:OrderRepository,
            order_item_repository:OrderItemRepository,
            product_repository:ProductRepository,
            # inventory_repository:InventoryRepository,
            inventory_service:InventoryService
    ):
        self.db = db

        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        self.inventory_service = inventory_service
        self.product_repository = product_repository

    def create_order(
            self,
            user_id:int,
            data:OrderCreate,
    ) -> Order:
        total = Decimal("0")
        seen_product = set()

        for item in data.items:
            if item.product_id in seen_product:
                raise DuplicateProductException()
            seen_product.add(item.product_id)

        # with self.db.begin():
        order = Order(
            user_id=user_id,
            total_amount=Decimal("0"),
            status = OrderStatus.PENDING,
        )

        order = self.order_repository.create(order)

        for item in data.items:
            product = self.product_repository.get_by_id(
                item.product_id,
            )
            if not product:
                raise ProductNotFoundException()

            self.inventory_service.reserve_stock(
            product_id=product.id,
            quantity=item.quantity,
            )

            order_item = OrderItem(
                    order_id = order.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=product.price,
            )
            self.order_item_repository.create(
                    order_item
            )


            total += (product.price * item.quantity)

        order.total_amount = total
        self.db.flush()
        self.db.refresh(order)

        return order
    
    def update_status(
            self,
            order_id:int,
            new_status:OrderStatus
    ) -> Order:

        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundExceptiion()
        allowed = VALID_TRANSITIONS[order.status]

        if new_status not in allowed:
            raise InvalidOrderStatusTransitionException()

        order.status = new_status
        return self.order_repository.update(order)