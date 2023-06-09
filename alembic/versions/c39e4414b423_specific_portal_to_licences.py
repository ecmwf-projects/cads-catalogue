"""specific portal to licences.

Revision ID: c39e4414b423
Revises: 10bbb7ddf032
Create Date: 2023-06-09 13:23:59.199638

"""
import sqlalchemy as sa

import alembic

# revision identifiers, used by Alembic.
revision = "c39e4414b423"
down_revision = "10bbb7ddf032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.add_column("licences", sa.Column("portal", sa.String))
    alembic.op.execute("UPDATE licences SET portal='c3s' where scope='portal'")


def downgrade() -> None:
    alembic.op.drop_column("licences", "portal")
