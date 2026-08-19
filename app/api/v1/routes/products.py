from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependecies.auth import required_roles
from app.db.session import get_db,get_auth_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductService
from app.core.exception import ProductNotFoundException
from app.application.services.product_application_service import ProdctApplicationService
from app.api.dependecies.service import get_product_application_service
router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    # db: Session = Depends(get_db),
    service:ProdctApplicationService = Depends(get_product_application_service),
    current_user: User = Depends(
        required_roles(
            UserRole.ADMIN,
            UserRole.STAFF,
        )
    )
):

    try:
        return service.create_product(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=list[ProductResponse])
def get_active_products(
    service: ProdctApplicationService = Depends(get_product_application_service),
):
    return service.get_active_products()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    service: ProdctApplicationService = Depends(get_product_application_service),
):
    try:
        return service.get_product(product_id)
    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )


@router.delete("/{product_id}", response_model=ProductResponse)
def deactivate_product(
    product_id: int,
    service: ProdctApplicationService = Depends(get_product_application_service),
    current_user: User = Depends(
        required_roles(UserRole.ADMIN, UserRole.STAFF)
    ),
):
    try:
        return service.deactivate_product(product_id)
    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )