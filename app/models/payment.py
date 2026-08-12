from decimal import Decimal
from app.models.payment_enums import PaymentStatus,PaymentProvider

from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import DateTime,func,String,ForeignKey,Numeric
from sqlalchemy.orm import relationship

class Payment(Base):
    __tablename__ = "payments"

    id:Mapped[int] = mapped_column(primary_key=True)

    order_id:Mapped[int] = mapped_column(ForeignKey("orders.id"),nullable=False)

    amount:Mapped[Decimal] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    provider:Mapped[PaymentProvider] = mapped_column(nullable=False)

    provider_payment_id:Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    status:Mapped[PaymentStatus] = mapped_column(
        nullable=False,
        server_default=PaymentStatus.PENDING.value)

    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    idempotency_key:Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    order = relationship(
        "Order",
        back_populates="payments"
    )