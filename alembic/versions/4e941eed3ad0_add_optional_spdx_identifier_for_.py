"""add optional spdx_identifier for licences

Revision ID: a81233756d0e
Revises: bc841f91fcbd
Create Date: 2025-07-21 11:19:14.168936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a81233756d0e'
down_revision = 'bc841f91fcbd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("licences", sa.Column("spdx_identifier", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("licences", "spdx_identifier")
