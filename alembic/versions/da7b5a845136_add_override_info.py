"""add override info.

Revision ID: da7b5a845136
Revises: cbf6bc621994
Create Date: 2024-02-16 15:03:54.461878

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "da7b5a845136"
down_revision = "cbf6bc621994"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "catalogue_updates",
        sa.Column("override_md", dialect_postgresql.JSONB, default={}),
    )


def downgrade() -> None:
    op.drop_column("catalogue_updates", "override_md")
