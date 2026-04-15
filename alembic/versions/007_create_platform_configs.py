"""create platform_configs table

Revision ID: 007
Revises: 006
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("api_key", sa.String(500), nullable=False, server_default=""),
        sa.Column("cookie", sa.String(5000), nullable=False, server_default=""),
        sa.Column("app_secret", sa.String(500), nullable=False, server_default=""),
        sa.Column("app_id", sa.String(200), nullable=False, server_default=""),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("platform_configs")
