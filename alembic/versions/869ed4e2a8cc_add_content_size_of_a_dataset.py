"""add content_size of a dataset.

Revision ID: 869ed4e2a8cc
Revises: efce9b3eb861
Create Date: 2025-08-08 15:03:45.276260

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "869ed4e2a8cc"
down_revision = "efce9b3eb861"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("content_size", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("resources", "content_size")
