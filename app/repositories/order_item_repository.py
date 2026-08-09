from sqlalchemy.orm import Session
from app.models.order_item import OrderItem

class OrderItemRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            item: OrderItem,
    ) -> OrderItem:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)

        return item

    def get_by_id(
            self,
            order_item_id: int,
    ) -> OrderItem | None:
        return (
            self.db.query(OrderItem)
            .filter(OrderItem.id == order_item_id)
            .first()
        )

    def get_by_order_id(
            self,
            order_id: int,
    ) -> list[OrderItem]:
        return (
            self.db.query(OrderItem)
            .filter(OrderItem.order_id == order_id)
            .all()
        )

    def update(
            self,
            order_item: OrderItem,
    ) -> OrderItem:
        self.db.flush()
        self.db.refresh(order_item)
        return order_item