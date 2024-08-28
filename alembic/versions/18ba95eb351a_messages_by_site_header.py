"""messages by SITE header.

Revision ID: 18ba95eb351a
Revises: 63827287c182
Create Date: 2024-07-15 17:08:21.290858

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "18ba95eb351a"
down_revision = "63827287c182"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("messages", "portal")
    op.add_column(
        "messages",
        sa.Column("site", sa.String, index=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "site")
    op.add_column(
        "messages",
        sa.Column("portal", sa.String, index=True),
    )
