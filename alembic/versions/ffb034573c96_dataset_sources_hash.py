"""dataset sources hash.

Revision ID: ffb034573c96
Revises: c39e4414b423
Create Date: 2023-06-26 10:50:52.670861

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ffb034573c96"
down_revision = "c39e4414b423"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("sources_hash", sa.String))


def downgrade() -> None:
    op.drop_column("resources", "sources_hash")
