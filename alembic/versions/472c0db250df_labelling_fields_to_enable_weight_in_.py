"""labelling fields to enable weight in full text search

Revision ID: 472c0db250df
Revises: 504bc78c19a5
Create Date: 2023-05-26 12:42:39.003076

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = '472c0db250df'
down_revision = '504bc78c19a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("resources", "fulltext_tsv")
    op.drop_index("idx_fulltext_tsv", "resources")
    op.add_column(
        'resources',
        sa.Column(
            "search_field",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "setweight(to_tsvector('english', coalesce(title, '')), 'A')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(abstract, '')), 'B')  || ' ' || "
                "setweight(to_tsvector('english', coalesce(fulltext, '')), 'C')",
                persisted=True,
            ),
        )
    )
    op.create_index('search_field', 'resources', postgresql_using='gin')
    # sql = """
    # ALTER TABLE resources
    # ADD COLUMN search_field tsvector GENERATED ALWAYS AS
    # (
    #     setweight(
    #         to_tsvector('english',
    #                     COALESCE(title, '')
    #                     ),
    #         'A') || ' ' ||
    #     setweight(
    #         to_tsvector('english',
    #                     COALESCE(abstract, '')
    #                     ),
    #         'B') || ' ' ||
    #     setweight(
    #         to_tsvector('english',
    #                     COALESCE(fulltext, '')
    #                     ),
    #         'C')
    # ) STORED;
    # """
    # op.execute(sql)


def downgrade() -> None:
    op.drop_column("resources", "search_field")
    op.drop_index("idx_search_field", "resources")
    op.add_column(
        'resources',
        sa.Column(
            "fulltext_tsv",
            sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
            sa.Computed(
                "to_tsvector('english', coalesce(title, '') || ' ' "
                "|| abstract || ' ' || coalesce(fulltext, ''))",
                persisted=True,
            ),
        )
    )
    op.create_index('idx_fulltext_tsv', 'resources', postgresql_using='gin')