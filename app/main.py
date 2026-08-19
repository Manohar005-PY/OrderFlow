import logging
import uuid

from fastapi import FastAPI
from app.api.v1.routes.auth import auth_router
from app.api.v1.routes.users import user_router
from app.api.v1.routes.products import router as product_router
from app.api.v1.routes.inventory import router as inventory_router
from app.api.v1.routes.order import router as order_router
from app.api.v1.routes.payments import router as payments_router
from app.api.health import router as health_router
from app.api.errors import (
    domain_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exception import OrderFlowException
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("orderflow")

app = FastAPI()
app.add_exception_handler(OrderFlowException, domain_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(product_router)
app.include_router(inventory_router)
app.include_router(order_router)
app.include_router(payments_router)
app.include_router(health_router)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response

@app.get("/")
def health_check():
    return{"status": "ok"}