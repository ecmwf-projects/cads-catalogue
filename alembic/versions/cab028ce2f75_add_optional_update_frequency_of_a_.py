"""add optional update_frequency of a dataset.

Revision ID: cab028ce2f75
Revises: b7bbdaf01165
Create Date: 2025-07-31 16:44:53.932974

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "cab028ce2f75"
down_revision = "b7bbdaf01165"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resources", sa.Column("update_frequency", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("resources", "update_frequency")
