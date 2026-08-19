from decimal import Decimal
from datetime import datetime

from sqlalchemy import Boolean,DateTime,Numeric, String,func,true
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base

class Product(Base):
    __tablename__ = "products" # table name

    id:Mapped[int] = mapped_column(primary_key=True) # product_id

    sku:Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    ) # unique string the product are represnented

    name:Mapped[str] = mapped_column(
        String(200),
        nullable=False
    ) # name of the product

    description:Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    ) # about the product

    price:Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        nullable=False
    ) # price of the item as decimal datatype.

    category:Mapped[str] = mapped_column(
        String(100),
        nullable=False
    ) # category of the product

    is_active:Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true()
    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    inventory = relationship("Inventory", back_populates="product", uselist=False)

    order_items = relationship(
    "OrderItem",
    back_populates="product",)