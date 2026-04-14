"""create revenue_records table

Revision ID: 006
Revises: 005
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revenue_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("distribution_id", sa.Integer(), sa.ForeignKey("distribution_records.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("generated_contents.id"), nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topics.id"), nullable=True),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="CNY"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_revenue_records_distribution_id", "revenue_records", ["distribution_id"])
    op.create_index("ix_revenue_records_platform", "revenue_records", ["platform"])


def downgrade() -> None:
    op.drop_table("revenue_records")
