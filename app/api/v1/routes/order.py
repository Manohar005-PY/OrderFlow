from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.api.dependecies.auth import (
    get_current_active_user,
)

from app.models.user import User

from app.schemas.order import (
    OrderCreate,
    OrderResponse
)

from app.repositories.order_item_repository import OrderItemRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.inventory_repository import InventoryRepository
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.schemas.order import OrderStatusUpdate

from app.core.exception import (
    ProductNotFoundException,
    InventoryNotFoundException,
    InsufficentStockException,
    DuplicateProductException
)

router = APIRouter(
    prefix="/order",
    tags=["Orders"]
)

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data:OrderCreate,
    current_user = Depends(get_current_active_user),
    db:Session = Depends(get_db),
):
    product_repository = ProductRepository(db)
    inventory_repository = InventoryRepository(db)

    inventory_service = InventoryService(
        inventory_repository=inventory_repository,
        product_repository=product_repository,
        db=db
    )

    service = OrderService(
        db=db,
        order_repository=OrderRepository(db),
        order_item_repository=OrderItemRepository(db),
        product_repository=product_repository,
        inventory_service=inventory_service
        )

    try:
        with db.begin(): 
            return service.create_order(
                current_user.id,
                data,
            )
    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found. "
        )
    except InventoryNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found. "
        )
    except InsufficentStockException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock. "
        )
    except DuplicateProductException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate product in order. "
        )

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    product_repository = ProductRepository(db)

    inventory_service = InventoryService(
        inventory_repository=InventoryRepository(db),
        product_repository=product_repository,
        db=db,
    )

    service = OrderService(
        db=db,
        order_repository=OrderRepository(db),
        order_item_repository=OrderItemRepository(db),
        product_repository=product_repository,
        inventory_service=inventory_service,
    )

    with db.begin():
        return service.update_status(
            order_id,
            data.status,
        )