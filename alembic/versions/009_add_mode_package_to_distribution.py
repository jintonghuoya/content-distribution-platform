"""add mode and package_data to distribution_records

Revision ID: 009
Revises: 008
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "distribution_records",
        sa.Column("mode", sa.String(20), nullable=False, server_default="published"),
    )
    op.add_column(
        "distribution_records",
        sa.Column("package_data", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("distribution_records", "package_data")
    op.drop_column("distribution_records", "mode")
