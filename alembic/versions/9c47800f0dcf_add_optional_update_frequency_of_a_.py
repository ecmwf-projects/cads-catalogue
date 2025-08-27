"""add optional update_frequency of a dataset.

Revision ID: 9c47800f0dcf
Revises: 0e6fa4b045eb
Create Date: 2025-08-27 10:30:14.689733

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9c47800f0dcf"
down_revision = "0e6fa4b045eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resources", sa.Column("update_frequency", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("resources", "update_frequency")
