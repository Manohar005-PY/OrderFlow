from sqlalchemy.orm import Session
from app.models.order_item import OrderItem

class OrderItemRepository:

    def __init__(self,db:Session):
        self.db = db

    def create(
            self,
            item:OrderItem,
    ) -> OrderItem:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)

        return item