"""new field 'site'.

Revision ID: 8ccbe515155c
Revises: 472c0db250df
Create Date: 2023-05-30 11:01:24.691827

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8ccbe515155c"
down_revision = "472c0db250df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("portal", sa.String, index=True))
    op.execute("UPDATE resources SET portal='c3s'")


def downgrade() -> None:
    op.drop_column("resources", "portal")
