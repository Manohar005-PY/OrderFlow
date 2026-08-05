from pydantic import BaseModel

class PaymentWebhook(BaseModel):
    provider_payment_id: str