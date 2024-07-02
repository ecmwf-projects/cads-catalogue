"""fields for advanced fts.

Revision ID: 63827287c182
Revises: 654a874249a8
Create Date: 2024-06-27 09:34:31.278052

"""

import sqlalchemy as sa
import sqlalchemy_utils

from alembic import op
from cads_catalogue import database

# revision identifiers, used by Alembic.
revision = "63827287c182"
down_revision = "654a874249a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resources",
        sa.Column(
            "fts",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "to_tsvector('english', coalesce(high_priority_terms, ''))",
                persisted=True,
            ),
        ),
    )
    op.create_index(
        "idx_resources_fts",
        "resources",
        ["fts"],
        postgresql_using="gin",
    )
    op.add_column("resources", sa.Column("popularity", sa.Integer, default=1))
    op.execute(database.add_rank_function_sql)


def downgrade() -> None:
    op.drop_column("resources", "fts")
    op.execute(database.drop_rank_function_sql)
