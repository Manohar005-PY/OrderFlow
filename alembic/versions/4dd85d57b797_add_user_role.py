"""add user role

Revision ID: 4dd85d57b797
Revises: 26a19d006580
Create Date: 2026-07-27 13:13:07.839728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4dd85d57b797'
down_revision: Union[str, Sequence[str], None] = '26a19d006580'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = sa.Enum(
    "ADMIN",
    "STAFF",
    "CUSTOMER",
    name="userrole"
)

def upgrade() -> None:
    # Create the PostgreSQL enum type
    user_role.create(op.get_bind(), checkfirst=True)

    # Add the column using that type
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role,
            nullable=False,
            server_default="CUSTOMER",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")

    # Remove the enum type
    user_role.drop(op.get_bind(), checkfirst=True)