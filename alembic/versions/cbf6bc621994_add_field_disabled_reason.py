"""add field disabled_reason.

Revision ID: cbf6bc621994
Revises: afe1900d489f
Create Date: 2024-02-09 14:25:09.295418

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "cbf6bc621994"
down_revision = "afe1900d489f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("disabled_reason", sa.String))


def downgrade() -> None:
    op.drop_column("resources", "disabled_reason")
