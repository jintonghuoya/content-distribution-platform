"""convert topics.status from enum to varchar

Revision ID: 008
Revises: 007
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL: convert ENUM column to VARCHAR via raw SQL
    # Step 1: Drop the default (must do before changing type)
    op.execute("ALTER TABLE topics ALTER COLUMN status DROP DEFAULT")
    # Step 2: Cast from enum to varchar
    op.execute("ALTER TABLE topics ALTER COLUMN status TYPE VARCHAR(22) USING status::VARCHAR")
    # Step 3: Re-add the default
    op.execute("ALTER TABLE topics ALTER COLUMN status SET DEFAULT 'pending'")
    # Step 4: Drop the now-unused enum type
    op.execute("DROP TYPE IF EXISTS topicstatus")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE topicstatus AS ENUM ('pending','filtered','rejected','generating','published')"
    )
    op.execute("ALTER TABLE topics ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE topics ALTER COLUMN status TYPE topicstatus USING status::topicstatus")
    op.execute("ALTER TABLE topics ALTER COLUMN status SET DEFAULT 'pending'")
