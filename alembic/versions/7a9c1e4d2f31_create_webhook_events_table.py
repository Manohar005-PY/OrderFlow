"""create webhook events table

Revision ID: 7a9c1e4d2f31
Revises: 4f6e8c2b1a90
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a9c1e4d2f31"
down_revision: Union[str, Sequence[str], None] = "4f6e8c2b1a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "webhook_events" in inspector.get_table_names():
        return
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "event_id"),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")