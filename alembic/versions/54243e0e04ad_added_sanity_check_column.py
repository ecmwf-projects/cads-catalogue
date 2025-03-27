"""added sanity_check column.

Revision ID: 54243e0e04ad
Revises: 1f965dd6fb7b
Create Date: 2025-03-13 11:22:32.844110

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "54243e0e04ad"
down_revision = "1f965dd6fb7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("sanity_check", dialect_postgresql.JSONB))


def downgrade() -> None:
    op.drop_column("resources", "sanity_check")
