"""multiple datasets repo.

Revision ID: 36caa987229e
Revises: 6ac5a2abf5f5
Create Date: 2024-12-27 11:12:14.551220

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

import alembic

# revision identifiers, used by Alembic.
revision = "36caa987229e"
down_revision = "6ac5a2abf5f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.drop_column("catalogue_updates", "metadata_repo_commit")
    alembic.op.add_column(
        "catalogue_updates",
        sa.Column("metadata_repo_commit", dialect_postgresql.JSONB, default={}),
    )


def downgrade() -> None:
    alembic.op.drop_column("catalogue_updates", "metadata_repo_commit")
    alembic.op.add_column(
        "catalogue_updates", sa.Column("metadata_repo_commit", sa.String)
    )
