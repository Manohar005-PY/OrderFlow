from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=5, max_length=1000)
    price: Decimal = Field(gt=0)
    category: str = Field(min_length=2, max_length=100)

from datetime import datetime


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    price: Decimal
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)