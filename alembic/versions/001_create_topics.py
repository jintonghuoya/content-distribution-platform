"""create topics table

Revision ID: 001
Revises:
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(200), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(1000), nullable=False, server_default=""),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("heat_value", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "status",
            sa.Enum("pending", "filtered", "rejected", "generating", "published", name="topicstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topics_title", "topics", ["title"])
    op.create_index("ix_topics_source", "topics", ["source"])
    op.create_index("ix_topics_status", "topics", ["status"])


def downgrade() -> None:
    op.drop_table("topics")
    op.execute("DROP TYPE IF EXISTS topicstatus")
