"""labelling fields to enable weight in full text search.

Revision ID: 472c0db250df
Revises: 504bc78c19a5
Create Date: 2023-05-26 12:42:39.003076

"""
import sqlalchemy as sa
import sqlalchemy_utils

from alembic import op

# revision identifiers, used by Alembic.
revision = "472c0db250df"
down_revision = "504bc78c19a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("resources", "fulltext_tsv")
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
        "idx_resources_search_field", "resources", ["search_field"], postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_column("resources", "search_field")
    op.add_column(
        "resources",
        sa.Column(
            "fulltext_tsv",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "to_tsvector('english', coalesce(title, '') || ' ' "
                "|| abstract || ' ' || coalesce(fulltext, ''))",
                persisted=True,
            ),
        ),
    )
    op.create_index(
        "idx_fulltext_tsv", "resources", ["fulltext_tsv"], postgresql_using="gin"
    )
