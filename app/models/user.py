from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime, func, true,Enum
from app.models.enums import UserRole
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__  = "users"

    id:Mapped[int] = mapped_column(primary_key=True)
    email:Mapped[str] = mapped_column(index=True,nullable=False, unique=True)
    hashed_password:Mapped[str] = mapped_column(nullable=False)
    full_name:Mapped[str] = mapped_column(nullable=False)
    role:Mapped[UserRole] = mapped_column(Enum(UserRole,name="userrole"),nullable=False,server_default=UserRole.CUSTOMER)
    is_active:Mapped[bool] = mapped_column(nullable=False, server_default=true())
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False,onupdate=func.now())

    orders = relationship(
    "Order",
    back_populates="user",)