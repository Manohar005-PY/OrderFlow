from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.application.services.inventory_application_service import InventoryApplicationService
from app.application.services.product_application_service import ProdctApplicationService

def get_inventory_application_service(
        db:Session = Depends(get_db),
) -> InventoryApplicationService:

    return InventoryApplicationService(db)

def get_product_application_service(
        db:Session = Depends(get_db)
) -> ProdctApplicationService:

    return ProdctApplicationService(db)