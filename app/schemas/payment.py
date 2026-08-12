from app.models.payment_enums  import PaymentProvider,PaymentStatus
from datetime import datetime
from pydantic import BaseModel,ConfigDict
from decimal import Decimal

class PaymentCreate(BaseModel):
    order_id: int
    provider: PaymentProvider
    idempotency_key:str

class PaymentResponse(BaseModel):
    id:int
    order_id:int
    amount:Decimal
    provider:PaymentProvider
    status:PaymentStatus
    provider_payment_id:str
    created_at:datetime

    model_config = ConfigDict(from_attributes=True)

class PaymentStatusUpdate(BaseModel):
    status:PaymentStatus