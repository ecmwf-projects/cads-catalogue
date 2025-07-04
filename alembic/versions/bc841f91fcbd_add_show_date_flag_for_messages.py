"""add show_date flag for messages.

Revision ID: bc841f91fcbd
Revises: 54243e0e04ad
Create Date: 2025-07-03 10:51:22.122358

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "bc841f91fcbd"
down_revision = "54243e0e04ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("show_date", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("messages", "show_date")
