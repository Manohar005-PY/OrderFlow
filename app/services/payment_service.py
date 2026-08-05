from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.payment import PaymentCreate
from app.models.payment_enums import PaymentStatus
from app.core.exception import OrderNotFoundExceptiion,PaymentAlreadyCompletedException,PaymentNotFoundException
from app.models.payment import Payment
from app.models.order_enums import OrderStatus
# from app.gateway.mock_gateway import MockGateway
from app.gateway.payment_gateway import PaymentGateway

class PaymentService:
    def __init__(
            self,
            payment_repository:PaymentRepository,
            order_repository:OrderRepository,
            gateway: PaymentGateway,
    ):
        self.payment_repository = payment_repository
        self.order_repository = order_repository
        self.gateway =gateway

    def create_payment(
            self,
            data:PaymentCreate,
    ) -> Payment:

        order = self.order_repository.get_by_id(
            data.order_id
        )

        if not order:
            raise OrderNotFoundExceptiion()

        payments = self.payment_repository.get_by_order_id(
            order.id
        )

        if any(payment .status == PaymentStatus.SUCCESS for payment in payments):
            raise PaymentAlreadyCompletedException()

        payment = Payment(
            order_id = order.id,
            amount = order.total_amount,
            provider = data.provider,
            status = PaymentStatus.PENDING,

        )
        provider_payment_id = self.gateway.create_payment(payment)

        payment.provider_payment_id = provider_payment_id

        return self.payment_repository.create(payment)
    
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
        
        verified = self.gateway.verify_payment(
            payment.provider_payment_id
        )

        if not verified:
            payment.status = PaymentStatus.FAILED
        return self.payment_repository.update(payment)

        payment.status = PaymentStatus.SUCCESS
        self.payment_repository.update(payment)

        order = self.order_repository.get_by_id(payment.order_id)

        if not order:
            raise OrderNotFoundExceptiion()

        order.status = OrderStatus.PAID
        self.order_repository.update(order)

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

        if payment.status == PaymentStatus.SUCCESS:
            return payment
        
        verified = self.gateway.verify_payment(
            provider_payment_id
        )

        if not verified:
            payment.status = PaymentStatus.FAILED
            return self.payment_repository.update(payment)

        if verified:
            payment.status = PaymentStatus.SUCCESS

        payment = self.payment_repository.update(payment)

        order = self.order_repository.get_by_id(
            payment.order_id
        )

        if not order:
            raise OrderNotFoundExceptiion()

        order.status = OrderStatus.PAID
        self.order_repository.update(order)
        return payment