"""add priority for contents.

Revision ID: 1f965dd6fb7b
Revises: c5b30a707329
Create Date: 2025-02-17 08:42:42.548390

"""

import sqlalchemy as sa

import alembic

# revision identifiers, used by Alembic.
revision = "1f965dd6fb7b"
down_revision = "c5b30a707329"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.add_column(
        "contents", sa.Column("priority", sa.Integer, default=0, nullable=True)
    )
    alembic.op.execute("UPDATE contents SET priority = 0")
    alembic.op.alter_column("contents", "priority", nullable=False)


def downgrade() -> None:
    alembic.op.drop_column("contents", "priority")
