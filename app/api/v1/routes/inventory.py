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
from app.schemas.inventory import StockOperation
from app.core.exception import (
    InventoryAlreadyexistsException,
    InventoryNotFoundException,
    InsufficentStockException,
    InvalidReservationException,
    ProductNotFoundException,
)
from app.application.services.inventory_application_service import InventoryApplicationService
from app.api.dependecies.service import get_inventory_application_service

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
    # db: Session = Depends(get_db),
    service:InventoryApplicationService = Depends(
        get_inventory_application_service
    ),
    current_user: User = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF,
        )
    ),
):
    # inventory_repository = InventoryRepository(db)
    # product_repository = ProductRepository(db)

    # service = InventoryService(
    # inventory_repository,
    # product_repository,
    # db
    # )
    try:
        return service.create_inventory(data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
    )
    except InventoryAlreadyexistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for product.",
        )
    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

@router.post(
    "/{product_id}/add-stock",
    response_model=InventoryResponse,
)
def add_stock(
    product_id: int,
    data: StockOperation,
    # db: Session = Depends(get_db),
    service:InventoryApplicationService = Depends(
        get_inventory_application_service
    ),
    current_user: User = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF,
        )
    ),
):
    # inventory_repository = InventoryRepository(db)
    # product_repository = ProductRepository(db)

    # service = InventoryService(
        # inventory_repository,
        # product_repository,
        # db
    # )

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

@router.post("/{product_id}/remove-stock",
             response_model=InventoryResponse,
             )
def remove_stock(
    product_id:int,
    data:StockOperation,
    service:InventoryApplicationService = Depends(
        get_inventory_application_service
    ),
    # db:Session = Depends(get_db),
    current_user = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF
        )
    )
):
    # inventory_repository = InventoryRepository(db)
    # product_repository = ProductRepository(db)

    # service = InventoryService(
        # inventory_repository,
        # product_repository,
        # db
    # )
    try:
        return service.remove_stock(
                product_id,
                data.quantity
            )
        
    except InventoryNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found."
        )
    except InsufficentStockException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficent avilable stock"
        )
@router.post(
    "/{product_id}/reserve-stock",
    response_model=InventoryResponse,
)
def reserve_stock(
    product_id:int,
    data:StockOperation,
    service:InventoryApplicationService = Depends(
        get_inventory_application_service
    ),
    # db:Session = Depends(get_db),
    current_user = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF
        )
    )
):
    # inventory_repository = InventoryRepository(db)
    # product_repository = ProductRepository(db)

    # service = InventoryService(
        # inventory_repository,
        # product_repository,
        # db
    # )

    try:
        # with db.begin():
            return service.reserve_stock(
                product_id,
                data.quantity,
            )
        
    except InventoryNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found. "
        )
    except InsufficentStockException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficent avilable stock",
        )

@router.post(
    "/{product_id}/release-stock",
    response_model=InventoryResponse,
)
def release_stock(
    product_id:int,
    data:StockOperation,
    # db:Session = Depends(get_db),
    service:InventoryApplicationService = Depends(
        get_inventory_application_service
    ),
    current_user = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF
        )
    )
):
    # inventory_repository = InventoryRepository(db)
    # product_repository = ProductRepository(db)

    # service = InventoryService(
        # inventory_repository,
        # product_repository,
        # db
    # )
    try:
        # with db.begin():
            return service.release_stock(
                product_id,
                data.quantity
            )
        
    except InventoryNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found. "
        )
    except InvalidReservationException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot release more than reserved quantity"
        )
