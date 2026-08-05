from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentProvider(str, Enum):
    STRIPE = "STRIPE"
    RAZORPAY = "RAZORPAY"
    PAYPAL = "PAYPAL"
    MOCK = "MOCK"