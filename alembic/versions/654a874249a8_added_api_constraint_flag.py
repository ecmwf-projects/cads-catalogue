"""added api constraint flag.

Revision ID: 654a874249a8
Revises: 7366df17e57c
Create Date: 2024-05-17 12:16:18.206589

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "654a874249a8"
down_revision = "7366df17e57c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("api_enforce_constraints", sa.Boolean))


def downgrade() -> None:
    op.drop_column("resources", "api_enforce_constraints")
