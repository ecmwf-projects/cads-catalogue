"""FAIR additions.

Revision ID: ddf161fdce37
Revises: 9c47800f0dcf
Create Date: 2025-09-17 13:42:00.808209

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql  # needed for mypy

from alembic import op

# revision identifiers, used by Alembic.
revision = "ddf161fdce37"
down_revision = "9c47800f0dcf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resource_data", sa.Column("fair_data", dialect_postgresql.JSONB))
    op.add_column(
        "resources",
        sa.Column(
            "fair_timestamp", sa.DateTime(timezone=True), default=None, nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("resource_data", "fair_data")
    op.drop_column("resources", "fair_timestamp")
