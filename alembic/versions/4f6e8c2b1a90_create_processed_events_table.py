"""create processed events table

Revision ID: 4f6e8c2b1a90
Revises: 024df5909cf5
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f6e8c2b1a90"
down_revision: Union[str, Sequence[str], None] = "024df5909cf5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processed_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("consumer_name", sa.String(length=100), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "consumer_name"),
    )


def downgrade() -> None:
    op.drop_table("processed_events")