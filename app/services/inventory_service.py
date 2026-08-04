from app.models.inventory import Inventory
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryCreate
from app.core.exception import InventoryAlreadyexistsException,InventoryNotFoundException,InsufficentStockException,InvalidReservationException,ProductNotFoundException

from sqlalchemy.orm import Session

class InventoryService:

    def __init__(self,
                 inventory_repository:InventoryRepository,product_repository:ProductRepository,
                 db:Session
            ) -> None:
        self.inventory_repository = inventory_repository
        self.product_repository = product_repository
        # self.db = db

    def create_inventory(self,data:InventoryCreate) -> Inventory:
        return self._create_inventory(data)
    
    def _create_inventory(self,data:InventoryCreate) -> Inventory:
        
        product = self.product_repository.get_by_id(data.product_id)

        if not product:
            raise ProductNotFoundException()
        existing = self.inventory_repository.get_by_product_id(data.product_id)
        if existing:
            raise InventoryAlreadyexistsException()
        inventory = Inventory(product_id = data.product_id,
                                quantity=data.quantity)
        inventory = self.inventory_repository.create(inventory)
        return inventory

    def add_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:
        return self._add_stock(product_id,quantity)
        
    def _add_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:
        inventory = self.inventory_repository.get_by_product_id(product_id)

        if not inventory:
            raise InventoryNotFoundException()

        inventory.quantity += quantity
        
        inventory =  self.inventory_repository.update(inventory)
        return inventory

    def remove_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:
        return self._remove_stock(product_id,quantity)
        
    def _remove_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:
        inventory = self.inventory_repository.get_by_product_id(product_id)
        if not inventory:
            raise InventoryNotFoundException()

        if inventory.available_quantity < quantity:
            raise InsufficentStockException()

        inventory.quantity -= quantity
        inventory = self.inventory_repository.update(inventory)
        return inventory
    
    def reserve_stock(
            self,
            product_id:int,
            quantity:int
    ) -> Inventory:
        return self._reserve_stock(product_id,quantity)
    
    def _reserve_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:

        inventory = self.inventory_repository.get_by_product_id(product_id)
        if not inventory:
            raise InventoryNotFoundException()
        if inventory.available_quantity < quantity:
            raise InsufficentStockException()

        inventory.reserved_quantity += quantity
        inventory = self.inventory_repository.update(inventory)
        return inventory
    def release_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:
        return self._reserve_stock(product_id,quantity)
        
    def _release_stock(
            self,
            product_id:int,
            quantity:int,
    ) -> Inventory:
        inventory = self.inventory_repository.get_by_product_id(product_id)

        if not inventory:
            raise InventoryNotFoundException()

        if inventory.reserved_quantity < quantity:
            raise InvalidReservationException()

        inventory.reserved_quantity -= quantity
        inventory = self.inventory_repository.update(inventory)
        return inventory