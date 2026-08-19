import json
from sqlalchemy.exc import IntegrityError

from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.order_item_repository import OrderItemRepository
from app.repositories.outbox_repository import OutboxRepository

from app.services.inventory_service import InventoryService

from app.schemas.payment import PaymentCreate
from app.models.payment_enums import PaymentStatus
from app.models.payment import Payment
from app.models.order_enums import OrderStatus
from app.models.outbox import OutboxEvent

from app.gateway.payment_gateway import PaymentGateway

from app.core.exception import (
    OrderNotFoundExceptiion,
    PaymentAlreadyCompletedException,
    PaymentNotFoundException,
    IdempotencyConflictException,
)


class PaymentService:

    def __init__(
        self,
        payment_repository: PaymentRepository,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
        inventory_service: InventoryService,
        gateway: PaymentGateway,
        outbox_repository: OutboxRepository,
    ):
        self.payment_repository = payment_repository
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        self.inventory_service = inventory_service
        self.gateway = gateway
        self.outbox_repository = outbox_repository

    def create_payment(
        self,
        data: PaymentCreate,
    ) -> Payment:

        existing = self.payment_repository.get_by_idempotency_key(
            data.idempotency_key
        )

        if existing:
            if existing.order_id != data.order_id or existing.provider != data.provider:
                raise IdempotencyConflictException()
            return existing

        order = self.order_repository.get_by_id(
            data.order_id
        )

        if not order:
            raise OrderNotFoundExceptiion()

        payments = self.payment_repository.get_by_order_id(
            order.id
        )

        if any(
            payment.status == PaymentStatus.SUCCESS
            for payment in payments
        ):
            raise PaymentAlreadyCompletedException()

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            provider=data.provider,
            status=PaymentStatus.PENDING,
            idempotency_key=data.idempotency_key,
        )

        provider_payment_id = self.gateway.create_payment(
            payment
        )

        payment.provider_payment_id = provider_payment_id

        try:
            with self.payment_repository.db.begin_nested():
                return self.payment_repository.create(payment)
        except IntegrityError:
            existing = self.payment_repository.get_by_idempotency_key(
                data.idempotency_key
            )
            if existing and (
                existing.order_id == data.order_id
                and existing.provider == data.provider
            ):
                return existing
            raise

    def confirm_payment(
        self,
        payment_id: int,
    ) -> Payment:

        payment = self.payment_repository.get_by_id(
            payment_id
        )

        if not payment:
            raise PaymentNotFoundException()

        if payment.status == PaymentStatus.SUCCESS:
            raise PaymentAlreadyCompletedException()

        if payment.status == PaymentStatus.FAILED:
            return payment

        verified = self.gateway.verify_payment(
            payment.provider_payment_id
        )

        if not verified:

            payment.status = PaymentStatus.FAILED
            self.payment_repository.update(payment)

            order = self.order_repository.get_by_id(
                payment.order_id
            )

            if not order:
                raise OrderNotFoundExceptiion()

            items = self.order_item_repository.get_by_order_id(
                order.id
            )

            for item in items:
                self.inventory_service.release_stock(
                    product_id=item.product_id,
                    quantity=item.quantity,
                )

            order.status = OrderStatus.CANCELLED
            self.order_repository.update(order)

            event = OutboxEvent(
                event_type="PaymentFailed",
                aggregate_type="Payment",
                aggregate_id=payment.id,
                payload=json.dumps({
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "amount": str(payment.amount),
                }),
            )

            self.outbox_repository.create(event)

            return payment

        payment.status = PaymentStatus.SUCCESS
        self.payment_repository.update(payment)

        order = self.order_repository.get_by_id(
            payment.order_id
        )

        if not order:
            raise OrderNotFoundExceptiion()

        order.status = OrderStatus.PAID
        self.order_repository.update(order)

        event = OutboxEvent(
            event_type="PaymentSucceeded",
            aggregate_type="Payment",
            aggregate_id=payment.id,
            payload=json.dumps({
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "amount": str(payment.amount),
            }),
        )

        self.outbox_repository.create(event)

        return payment

    def process_webhook(
        self,
        provider_payment_id: str,
    ) -> Payment:

        payment = self.payment_repository.get_by_provider_payment_id(
            provider_payment_id
        )

        if not payment:
            raise PaymentNotFoundException()

        if payment.status in (
            PaymentStatus.SUCCESS,
            PaymentStatus.FAILED,
        ):
            return payment

        verified = self.gateway.verify_payment(
            provider_payment_id
        )

        if not verified:

            payment.status = PaymentStatus.FAILED
            self.payment_repository.update(payment)

            order = self.order_repository.get_by_id(
                payment.order_id
            )

            if not order:
                raise OrderNotFoundExceptiion()

            items = self.order_item_repository.get_by_order_id(
                order.id
            )

            for item in items:
                self.inventory_service.release_stock(
                    product_id=item.product_id,
                    quantity=item.quantity,
                )

            order.status = OrderStatus.CANCELLED
            self.order_repository.update(order)

            event = OutboxEvent(
                event_type="PaymentFailed",
                aggregate_type="Payment",
                aggregate_id=payment.id,
                payload=json.dumps({
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "amount": str(payment.amount),
                }),
            )

            self.outbox_repository.create(event)

            return payment

        payment.status = PaymentStatus.SUCCESS
        self.payment_repository.update(payment)

        order = self.order_repository.get_by_id(
            payment.order_id
        )

        if not order:
            raise OrderNotFoundExceptiion()

        order.status = OrderStatus.PAID
        self.order_repository.update(order)

        event = OutboxEvent(
            event_type="PaymentSucceeded",
            aggregate_type="Payment",
            aggregate_id=payment.id,
            payload=json.dumps({
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "amount": str(payment.amount),
            }),
        )

        self.outbox_repository.create(event)

        return payment