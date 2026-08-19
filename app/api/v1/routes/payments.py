from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.services.inventory_service import InventoryService
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.order_item_repository import OrderItemRepository
from app.gateway.mock_gateway import MockGateway
from app.services.payment_service import PaymentService
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.core.exception import (
    OrderNotFoundExceptiion,
    IdempotencyConflictException,
    PaymentAlreadyCompletedException,
    PaymentNotFoundException,
    WebhookVerificationException,
)
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.webhook_event_repository import WebhookEventRepository
from app.webhook.dependencies import webhook_verifier_dependency
from app.webhook.verifier import ProviderWebhookVerifier

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


def get_payment_service(db: Session) -> PaymentService:
    product_repository = ProductRepository(db)
    inventory_repository = InventoryRepository(db)
    inventory_service = InventoryService(inventory_repository, product_repository)

    return PaymentService(
        payment_repository=PaymentRepository(db),
        order_repository=OrderRepository(db),
        order_item_repository=OrderItemRepository(db),
        inventory_service=inventory_service,
        gateway=MockGateway(),
        outbox_repository=OutboxRepository(db),
    )


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
):
    service = get_payment_service(db)

    try:
        with db.begin():
            return service.create_payment(data)
    except OrderNotFoundExceptiion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    except PaymentAlreadyCompletedException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already completed.",
        )
    except IdempotencyConflictException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key was already used for different payment data.",
        )


@router.post(
    "/{payment_id}/confirm",
    response_model=PaymentResponse,
)
def confirm_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    service = get_payment_service(db)

    try:
        with db.begin():
            return service.confirm_payment(payment_id)
    except PaymentNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )
    except OrderNotFoundExceptiion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    except PaymentAlreadyCompletedException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already completed.",
        )


@router.post(
    "/webhook",
    response_model=PaymentResponse,
)
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
    verifier: ProviderWebhookVerifier = Depends(webhook_verifier_dependency),
):
    signature = request.headers.get("Stripe-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature.",
        )

    try:
        event = verifier.verify(
            await request.body(),
            signature,
        )
    except WebhookVerificationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    event_id = event["id"]
    event_data = event.get("data", {}).get("object", event)
    provider_payment_id = event_data.get("provider_payment_id")
    if not provider_payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook event is missing provider payment ID.",
        )

    service = get_payment_service(db)
    webhook_events = WebhookEventRepository(db)
    payments = PaymentRepository(db)

    try:
        with db.begin():
            existing = webhook_events.get("stripe", event_id)
            if existing:
                payment = payments.get_by_provider_payment_id(provider_payment_id)
                if not payment:
                    raise PaymentNotFoundException()
                return payment

            payment = service.process_webhook(provider_payment_id)
            try:
                with db.begin_nested():
                    webhook_events.create("stripe", event_id)
            except IntegrityError:
                pass
            return payment
    except PaymentNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )
    except OrderNotFoundExceptiion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )