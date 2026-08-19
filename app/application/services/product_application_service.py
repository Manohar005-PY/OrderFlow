from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate
from app.services.product_service import ProductService

class ProdctApplicationService:
    def __init__(
            self,
            db:Session,
        ):

        self.db = db
        repository  = ProductRepository(db)
        self.product_service = ProductService(
            repository,
            db
        )

    def create_product(self,product:ProductCreate):
        with self.db.begin():
            return self.product_service.create_product(
                product
            )

    def get_product(self, product_id: int):
        return self.product_service.get_product(product_id)

    def get_active_products(self):
        return self.product_service.get_active_products()

    def deactivate_product(self, product_id: int):
        with self.db.begin():
            return self.product_service.deactivate_product(product_id)