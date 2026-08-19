from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate
from app.core.exception import ProductNotFoundException

from sqlalchemy.orm import Session

class ProductService:
    def __init__(self,
        repository: ProductRepository,
        db:Session
    ):
    
        self.repository = repository
        self.db = db

    def create_product(self, product_data: ProductCreate) -> Product:
        existing = self.repository.get_by_sku(product_data.sku)
        if existing:
            raise ValueError("Product SKU already exists")
        product = Product(
                sku=product_data.sku,
                name=product_data.name,
                description=product_data.description,
                price=product_data.price,
                category=product_data.category,
            )
        product = self.repository.create(product)

        return product

    def get_product(self, product_id: int) -> Product:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundException()
        return product

    def get_active_products(self) -> list[Product]:
        return self.repository.get_all()

    def deactivate_product(self, product_id: int) -> Product:
        product = self.get_product(product_id)
        return self.repository.deactivate(product)