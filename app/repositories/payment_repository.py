from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.payment_enums import PaymentStatus


class PaymentRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        payment: Payment,
    ) -> Payment:

        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)

        return payment

    def get_by_id(
        self,
        payment_id: int,
    ) -> Payment | None:

        return (
            self.db.query(Payment)
            .filter(Payment.id == payment_id)
            .first()
        )

    def get_by_order_id(
        self,
        order_id: int,
    ) -> list[Payment]:

        return (
            self.db.query(Payment)
            .filter(Payment.order_id == order_id)
            .all()
        )

    def update(
        self,
        payment: Payment,
    ) -> Payment:

        self.db.flush()
        self.db.refresh(payment)

        return payment
    
    def get_by_provider_payment_id(
            self,
            provider_payment_id:str
    ) -> Payment |None:
        return(
            self.db.query(Payment)
            .filter(
                Payment.provider_payment_id == provider_payment_id
            )
            .first()
        )
    def get_by_idempotency_key(
            self,
            key:str
    )-> Payment | None:
        
        return (
            self.db.query(Payment)
            .filter(
                Payment.idempotency_key == key
            )
            .first()
        )