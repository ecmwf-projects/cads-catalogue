"""support cim repo hash.

Revision ID: 3c57748c209b
Revises: ffb034573c96
Create Date: 2023-07-26 11:10:11.786684

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3c57748c209b"
down_revision = "ffb034573c96"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalogue_updates", sa.Column("cim_repo_commit", sa.String))


def downgrade() -> None:
    op.drop_column("catalogue_updates", "cim_repo_commit")
