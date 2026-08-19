import logging
from http import HTTPStatus

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.exception import (
    DuplicateProductException,
    IdempotencyConflictException,
    InsufficentStockException,
    InvalidOrderStatusTransitionException,
    InvalidReservationException,
    InventoryAlreadyexistsException,
    InventoryNotFoundException,
    OrderFlowException,
    OrderNotFoundExceptiion,
    PaymentAlreadyCompletedException,
    PaymentNotFoundException,
    ProductNotFoundException,
)

logger = logging.getLogger("orderflow.errors")


DOMAIN_ERRORS = {
    ProductNotFoundException: (404, "product_not_found", "Product not found"),
    InventoryNotFoundException: (404, "inventory_not_found", "Inventory not found"),
    OrderNotFoundExceptiion: (404, "order_not_found", "Order not found"),
    PaymentNotFoundException: (404, "payment_not_found", "Payment not found"),
    InventoryAlreadyexistsException: (
        409,
        "inventory_already_exists",
        "Inventory already exists for product",
    ),
    IdempotencyConflictException: (
        409,
        "idempotency_conflict",
        "Idempotency key was already used for different payment data",
    ),
    PaymentAlreadyCompletedException: (
        409,
        "payment_already_completed",
        "Payment already completed",
    ),
    DuplicateProductException: (
        400,
        "duplicate_product",
        "Product appears more than once in the order",
    ),
    InsufficentStockException: (
        400,
        "insufficient_stock",
        "Insufficient stock",
    ),
    InvalidReservationException: (
        400,
        "invalid_reservation",
        "Invalid inventory reservation",
    ),
    InvalidOrderStatusTransitionException: (
        400,
        "invalid_order_status_transition",
        "Invalid order status transition",
    ),
}


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def error_response(
    request: Request,
    status_code: int,
    error: str,
    message: str,
    details=None,
    headers=None,
) -> JSONResponse:
    content = {
        "error": error,
        "message": message,
        "request_id": request_id(request),
    }
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content, headers=headers)


async def domain_exception_handler(request: Request, exc: OrderFlowException):
    status_code, error, message = DOMAIN_ERRORS.get(
        type(exc),
        (400, "business_error", "The requested operation is not valid"),
    )
    return error_response(request, status_code, error, message)


async def http_exception_handler(request: Request, exc: HTTPException):
    status_code = exc.status_code
    default_error = HTTPStatus(status_code).phrase.lower().replace(" ", "_")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return error_response(
        request,
        status_code,
        f"http_{default_error}",
        message,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        request,
        422,
        "validation_error",
        "Request validation failed",
        details=jsonable_encoder(exc.errors()),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled application error",
        extra={"request_id": request_id(request)},
    )
    return error_response(
        request,
        500,
        "internal_server_error",
        "An unexpected error occurred",
    )
