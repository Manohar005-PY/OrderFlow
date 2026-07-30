from sqlalchemy.orm import Session

from app.models.inventory import Inventory

class InventoryRepository:

    def __init__(self,db:Session):
        self.db = db

    def create(self,inventory:Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def get_by_product_id(self,product_id:int) -> Inventory:
        
        inventory = self.db.query(Inventory).filter(Inventory.product_id == product_id).first()

        return inventory

    def update(self,inventory:Inventory) -> Inventory:
        self.db.commit()
        self.db.refresh(inventory)

        return inventory
    