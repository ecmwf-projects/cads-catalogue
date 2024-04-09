"""new column qos_tags.

Revision ID: 4947a1be081e
Revises: 875f93f41d79
Create Date: 2023-08-30 11:55:00.678617

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "4947a1be081e"
down_revision = "875f93f41d79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resources", sa.Column("qos_tags", dialect_postgresql.ARRAY(sa.String))
    )


def downgrade() -> None:
    op.drop_column("resources", "qos_tags")
