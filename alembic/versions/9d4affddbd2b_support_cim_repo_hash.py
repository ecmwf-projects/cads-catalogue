"""support cim repo hash.

Revision ID: 9d4affddbd2b
Revises: e5e9a8a41828
Create Date: 2023-07-26 11:20:16.888415

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9d4affddbd2b"
down_revision = "e5e9a8a41828"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalogue_updates", sa.Column("cim_repo_commit", sa.String))


def downgrade() -> None:
    op.drop_column("catalogue_updates", "cim_repo_commit")
