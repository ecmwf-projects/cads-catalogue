"""adding column for sanity check configuration.

Revision ID: b7bbdaf01165
Revises: bc841f91fcbd
Create Date: 2025-07-18 09:24:35.270818

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

import alembic

# revision identifiers, used by Alembic.
revision = "b7bbdaf01165"
down_revision = "bc841f91fcbd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.add_column(
        "resources",
        sa.Column("sanity_check_conf", dialect_postgresql.JSONB),
    )


def downgrade() -> None:
    alembic.op.drop_column("resources", "sanity_check_conf")
