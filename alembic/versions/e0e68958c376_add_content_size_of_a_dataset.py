"""add content_size of a dataset.

Revision ID: e0e68958c376
Revises: efce9b3eb861
Create Date: 2025-08-07 10:26:09.831462

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e0e68958c376"
down_revision = "efce9b3eb861"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("content_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("resources", "content_size")
