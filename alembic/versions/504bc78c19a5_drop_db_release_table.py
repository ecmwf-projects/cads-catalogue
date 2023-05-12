"""drop db_release table

Revision ID: 504bc78c19a5
Revises: 
Create Date: 2023-05-11 17:16:19.646769

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '504bc78c19a5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('db_release')


def downgrade() -> None:
    pass
