"""add new field adaptor_properties_hash.

Revision ID: e5e9a8a41828
Revises: ffb034573c96
Create Date: 2023-07-25 16:07:47.059717

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5e9a8a41828"
down_revision = "ffb034573c96"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("adaptor_properties_hash", sa.String))


def downgrade() -> None:
    op.drop_column("resources", "adaptor_properties_hash")
