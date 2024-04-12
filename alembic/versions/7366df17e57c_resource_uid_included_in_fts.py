"""resource_uid included in FTS.

Revision ID: 7366df17e57c
Revises: 81993949dc59
Create Date: 2024-04-11 14:11:50.174472

"""

import sqlalchemy as sa
import sqlalchemy_utils

from alembic import op

# revision identifiers, used by Alembic.
revision = "7366df17e57c"
down_revision = "81993949dc59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("resources", "search_field")
    op.add_column(
        "resources",
        sa.Column(
            "search_field",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "setweight(to_tsvector('english', resource_uid || ' ' || coalesce(title, '')), 'A') "
                " || ' ' || "
                "setweight(to_tsvector('english', coalesce(abstract, '')), 'B')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(fulltext, '')), 'C')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(high_priority_terms, '')), 'D')",
                persisted=True,
            ),
        ),
    )
    op.create_index(
        "idx_resources_search_field",
        "resources",
        ["search_field"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_column("resources", "search_field")
    op.add_column(
        "resources",
        sa.Column(
            "search_field",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "setweight(to_tsvector('english', coalesce(title, '')), 'A')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(abstract, '')), 'B')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(fulltext, '')), 'C')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(high_priority_terms, '')), 'D')",
                persisted=True,
            ),
        ),
    )
    op.create_index(
        "idx_resources_search_field",
        "resources",
        ["search_field"],
        postgresql_using="gin",
    )
