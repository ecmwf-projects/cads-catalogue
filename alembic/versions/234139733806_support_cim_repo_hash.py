"""support cim repo hash

Revision ID: 234139733806
Revises: ffb034573c96
Create Date: 2023-07-04 14:20:31.088075

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '234139733806'
down_revision = 'ffb034573c96'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalogue_updates", sa.Column("cim_repo_commit", sa.String))


def downgrade() -> None:
    op.drop_column("catalogue_updates", "cim_repo_commit")
