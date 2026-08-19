from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime, func, true,Enum
from app.models.enums import UserRole
from sqlalchemy.orm import relationship
# This is the user table

class User(Base):
    __tablename__  = "users"

    id:Mapped[int] = mapped_column(primary_key=True) #user_id
    email:Mapped[str] = mapped_column(index=True,nullable=False, unique=True) #email and its is unique
    hashed_password:Mapped[str] = mapped_column(nullable=False) # not a real password cause we always store the hashedpassword
    full_name:Mapped[str] = mapped_column(nullable=False) # users_full_name
    role:Mapped[UserRole] = mapped_column(Enum(UserRole,name="userrole"),nullable=False,server_default=UserRole.CUSTOMER) # this helps to decide what routes are accessed depending on the role
    is_active:Mapped[bool] = mapped_column(nullable=False, server_default=true()) # cheack weather the user is active or not
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False) # stroes the created at time depending on the timezone
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False,onupdate=func.now()) # whenever the row is updated, recent time is stored.

    orders = relationship(
    "Order",
    back_populates="user",) # this table is linked to orders table.