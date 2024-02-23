"""add high_priority_terms.

Revision ID: 81993949dc59
Revises: da7b5a845136
Create Date: 2024-02-22 17:53:46.392716

"""
import sqlalchemy as sa
import sqlalchemy_utils

from alembic import op


# revision identifiers, used by Alembic.
revision = '81993949dc59'
down_revision = 'da7b5a845136'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("resources", "search_field")
    op.add_column("resources", sa.Column("high_priority_terms", sa.String))
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


def downgrade() -> None:
    op.drop_column("resources", "search_field")
    op.drop_column("resources", "high_priority_terms")
    op.add_column(
        "resources",
        sa.Column(
            "search_field",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "setweight(to_tsvector('english', coalesce(title, '')), 'A')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(abstract, '')), 'B')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(fulltext, '')), 'C')",
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
