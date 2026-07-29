from sqlalchemy.orm import Session
from sqlalchemy import true

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_by_id(self, product_id: int) -> Product | None:
        return (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

    def get_by_sku(self, sku: str) -> Product | None:
        return (
            self.db.query(Product)
            .filter(Product.sku == sku)
            .first()
        )

    def get_all(self) -> list[Product]:
        return (
            self.db.query(Product)
            .filter(Product.is_active == true())
            .all()
        )

    def deactivate(self, product: Product) -> Product:
        product.is_active = False
        self.db.commit()
        self.db.refresh(product)
        return product
