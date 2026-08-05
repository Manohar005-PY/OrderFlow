from abc import ABC, abstractmethod

from app.models.payment import Payment


class PaymentGateway(ABC):

    @abstractmethod
    def create_payment(
        self,
        payment: Payment,
    ) -> str:
        pass

    @abstractmethod
    def verify_payment(
        self,
        provider_payment_id: str,
    ) -> bool:
        pass