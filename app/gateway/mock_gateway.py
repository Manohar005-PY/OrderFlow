import uuid
from app.gateway.payment_gateway import PaymentGateway

from app.models.payment import Payment


class MockGateway(PaymentGateway):

    def __init__(self, verify_result: bool = True):
        self.verify_result = verify_result

    def create_payment(
        self,
        payment: Payment,
    ) -> str:

        return str(uuid.uuid4())

    def verify_payment(
        self,
        provider_payment_id: str,
    ) -> bool:
        return self.verify_result