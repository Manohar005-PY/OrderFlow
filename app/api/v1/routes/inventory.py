from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependecies.auth import required_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryCreate, InventoryResponse, StockOperation
from app.services.inventory_service import InventoryService

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)

@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF,
        )
    ),
):
    inventory_repository = InventoryRepository(db)
    product_repository = ProductRepository(db)

    service = InventoryService(
    inventory_repository,
    product_repository,
    )
    try:
        return service.create_inventory(data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
    )

@router.post(
    "/{product_id}/add-stock",
    response_model=InventoryResponse,
)
def add_stock(
    product_id: int,
    data: StockOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF,
        )
    ),
):
    inventory_repository = InventoryRepository(db)
    product_repository = ProductRepository(db)

    service = InventoryService(
        inventory_repository,
        product_repository
    )

    try:
        return service.add_stock(
            product_id,
            data.quantity
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )