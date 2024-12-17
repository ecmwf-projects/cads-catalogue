"""add boolean flag to hidden contents.

Revision ID: 6ac5a2abf5f5
Revises: e5875ac4a047
Create Date: 2024-12-17 10:26:33.649562

"""

import sqlalchemy as sa

import alembic

# revision identifiers, used by Alembic.
revision = "6ac5a2abf5f5"
down_revision = "e5875ac4a047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.add_column(
        "contents", sa.Column("hidden", sa.Boolean, default=True, nullable=True)
    )
    alembic.op.execute("UPDATE contents SET hidden = FALSE")
    alembic.op.alter_column("contents", "hidden", nullable=False)


def downgrade() -> None:
    alembic.op.drop_column("contents", "hidden")
