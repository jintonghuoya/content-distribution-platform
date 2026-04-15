"""convert topics.status from enum to varchar

Revision ID: 008
Revises: 007
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert topics.status from native PostgreSQL enum to VARCHAR(22)
    op.alter_column(
        "topics",
        "status",
        type_=sa.String(22),
        existing_type=sa.Enum("pending", "filtered", "rejected", "generating", "published", name="topicstatus"),
        existing_nullable=False,
        existing_server_default="pending",
    )
    # Drop the now-unused enum type
    op.execute("DROP TYPE IF EXISTS topicstatus")


def downgrade() -> None:
    # Recreate the enum type
    topicstatus = sa.Enum("pending", "filtered", "rejected", "generating", "published", name="topicstatus")
    topicstatus.create(op.get_bind())
    op.alter_column(
        "topics",
        "status",
        type_=topicstatus,
        existing_type=sa.String(22),
        existing_nullable=False,
        existing_server_default="pending",
    )
