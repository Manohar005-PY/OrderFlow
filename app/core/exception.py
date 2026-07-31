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