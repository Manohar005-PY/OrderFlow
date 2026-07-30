from app.models.inventory import Inventory
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryCreate

class InventoryService:

    def __init__(self,inventory_repository:InventoryRepository,product_repository:ProductRepository) -> None:
        self.inventory_repository = inventory_repository
        self.product_repository = product_repository

    def create_inventory(self,data:InventoryCreate) -> Inventory:
        
        product = self.product_repository.get_by_id(data.product_id)

        if not product:
            raise ValueError("Product not Found")
        existing = self.inventory_repository.get_by_product_id(data.product_id)
        if existing:
            raise ValueError("Inventory already exists.")
        inventory = Inventory(product_id = data.product_id,
                              quantity=data.quantity)
        return self.inventory_repository.create(inventory)
    