"""add source repo commit.

Revision ID: ccdb8e308d41
Revises: 9d4affddbd2b
Create Date: 2023-08-07 10:22:16.865880

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ccdb8e308d41"
down_revision = "9d4affddbd2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalogue_updates", sa.Column("metadata_repo_commit", sa.String))


def downgrade() -> None:
    op.drop_column("catalogue_updates", "metadata_repo_commit")
