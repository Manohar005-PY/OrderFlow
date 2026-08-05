class OrderFlowException(Exception):
    """ Base exception for the application"""

class ProductNotFoundException(OrderFlowException):
    pass

class InventoryNotFoundException(OrderFlowException):
    pass

class InventoryAlreadyexistsException(OrderFlowException):
    pass

class InsufficentStockException(OrderFlowException):
    pass
class InvalidReservationException(OrderFlowException):
    pass
class DuplicateProductException(OrderFlowException):
    pass
class InvalidOrderStatusTransitionException(OrderFlowException):
    pass
class OrderNotFoundExceptiion(OrderFlowException):
    pass
class PaymentNotFoundException(OrderFlowException):
    pass
class PaymentAlreadyCompletedException(OrderFlowException):
    pass
class InvalidPaymnetStateException(OrderFlowException):
    pass