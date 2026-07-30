from decimal import Decimal
from datetime import datetime

from sqlalchemy import Boolean,DateTime,Numeric, String,func,true
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id:Mapped[int] = mapped_column(primary_key=True)

    sku:Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    name:Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description:Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    price:Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    category:Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

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