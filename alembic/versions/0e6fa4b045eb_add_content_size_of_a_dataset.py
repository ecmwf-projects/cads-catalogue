"""add content_size of a dataset.

Revision ID: 0e6fa4b045eb
Revises: a41235042d55
Create Date: 2025-08-26 14:36:06.698272

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0e6fa4b045eb"
down_revision = "a41235042d55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("content_size", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("resources", "content_size")
