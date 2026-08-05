from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.gateway.mock_gateway import MockGateway
from app.services.payment_service import PaymentService
from app.schemas.webhook import PaymentWebhook
from app.schemas.payment import PaymentResponse
from app.core.exception import PaymentNotFoundException, OrderNotFoundExceptiion

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/webhook",
    response_model=PaymentResponse,
)
def payment_webhook(
    data: PaymentWebhook,
    db: Session = Depends(get_db),
):
    payment_repository = PaymentRepository(db)
    order_repository = OrderRepository(db)
    gateway = MockGateway()

    service = PaymentService(
        payment_repository=payment_repository,
        order_repository=order_repository,
        gateway=gateway,
    )

    try:
        with db.begin():
            return service.process_webhook(
                data.provider_payment_id
            )
    except PaymentNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    except OrderNotFoundExceptiion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")