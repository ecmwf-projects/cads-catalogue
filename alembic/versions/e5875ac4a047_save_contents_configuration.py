"""save contents configuration.

Revision ID: e5875ac4a047
Revises: 694fde86c48c
Create Date: 2024-12-05 14:20:53.059624

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5875ac4a047"
down_revision = "694fde86c48c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "catalogue_updates",
        sa.Column("contents_config", dialect_postgresql.JSONB, default={}),
    )


def downgrade() -> None:
    op.drop_column("catalogue_updates", "contents_config")
