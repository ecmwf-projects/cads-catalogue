"""add column qa_flag.

Revision ID: afe1900d489f
Revises: 6a53ad750543
Create Date: 2023-12-11 09:38:04.421139

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "afe1900d489f"
down_revision = "6a53ad750543"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("qa_flag", sa.Boolean))


def downgrade() -> None:
    op.drop_column("resources", "qa_flag")
