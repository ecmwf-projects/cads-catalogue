"""new column qos_tags.

Revision ID: 74b759d224b7
Revises: fe3054fbc892
Create Date: 2023-08-11 13:55:00.678617

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "74b759d224b7"
down_revision = "fe3054fbc892"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resources", sa.Column("qos_tags", dialect_postgresql.ARRAY(sa.String))
    )


def downgrade() -> None:
    op.drop_column("resources", "qos_tags")
