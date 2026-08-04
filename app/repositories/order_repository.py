from sqlalchemy.orm import Session
from app.models.order import Order

class OrderRepository:

    def __init__(self,db:Session):
        self.db = db

    def create(
            self,
            order:Order
    ) -> Order:
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)

        return order
    
    def get_by_id(
            self,
            order_id:int
    ) -> Order | None:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        return order

    def update(
            self,
            order:Order,
    ) ->Order:
        self.db.flush()
        self.db.refresh(order)
        return order

    