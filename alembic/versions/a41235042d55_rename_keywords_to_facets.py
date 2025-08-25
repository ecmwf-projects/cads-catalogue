"""rename keywords to facets and add keywords_urls column.

Revision ID: a41235042d55
Revises: efce9b3eb861
Create Date: 2025-08-11 15:30:41.105369

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a41235042d55"
down_revision = "efce9b3eb861"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("keywords", "facets")
    op.alter_column("facets", "keyword_id", new_column_name="facet_id")
    op.alter_column("facets", "keyword_name", new_column_name="facet_name")

    op.rename_table("resources_keywords", "resources_facets")
    op.alter_column("resources_facets", "keyword_id", new_column_name="facet_id")

    op.add_column(
        "resources",
        sa.Column("keywords_urls", sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.alter_column("resources_facets", "facet_id", new_column_name="keyword_id")
    op.rename_table("resources_facets", "resources_keywords")

    op.alter_column("facets", "facet_id", new_column_name="keyword_id")
    op.alter_column("facets", "facet_name", new_column_name="keyword_name")
    op.rename_table("facets", "keywords")

    op.drop_column("resources", "keywords_urls")
