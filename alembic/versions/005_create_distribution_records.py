"""create distribution_records table

Revision ID: 005
Revises: 004
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "distribution_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("generated_contents.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("platform_content_id", sa.String(200), nullable=False, server_default=""),
        sa.Column("platform_url", sa.String(1000), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_distribution_records_content_id", "distribution_records", ["content_id"])
    op.create_index("ix_distribution_records_platform", "distribution_records", ["platform"])


def downgrade() -> None:
    op.drop_table("distribution_records")
