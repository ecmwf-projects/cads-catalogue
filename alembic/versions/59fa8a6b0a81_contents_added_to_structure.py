"""contents added to structure.

Revision ID: 59fa8a6b0a81
Revises: 18ba95eb351a
Create Date: 2024-09-02 11:34:57.475654

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as dialect_postgresql

import alembic

# revision identifiers, used by Alembic.
revision = "59fa8a6b0a81"
down_revision = "18ba95eb351a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.create_table(
        "contents",
        sa.Column("content_id", sa.Integer, primary_key=True),
        sa.Column("content_uid", sa.String, index=True, unique=True, nullable=False),
        sa.Column("content_update", sa.TIMESTAMP, nullable=False),
        sa.Column("data", dialect_postgresql.JSONB),
        sa.Column("description", sa.String, nullable=False),
        sa.Column("image", sa.String),
        sa.Column("layout", sa.String),
        sa.Column("link", sa.String),
        sa.Column("publication_date", sa.TIMESTAMP, nullable=False),
        sa.Column("site", sa.String, index=True, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
    )
    alembic.op.create_table(
        "content_keywords",
        sa.Column("keyword_id", sa.Integer, primary_key=True),
        sa.Column("category_name", sa.String),
        sa.Column("category_value", sa.String),
        sa.Column("keyword_name", sa.String),
    )
    alembic.op.create_table(
        "contents_keywords_m2m",
        sa.Column(
            "content_id",
            sa.Integer,
            sa.ForeignKey("contents.content_id"),
            primary_key=True,
        ),
        sa.Column(
            "keyword_id",
            sa.Integer,
            sa.ForeignKey("content_keywords.keyword_id"),
            primary_key=True,
        ),
    )
    alembic.op.add_column(
        "catalogue_updates", sa.Column("content_repo_commit", sa.String)
    )


def downgrade() -> None:
    alembic.op.drop_table("contents_keywords_m2m")
    alembic.op.drop_table("content_keywords")
    alembic.op.drop_table("contents")
    alembic.op.drop_column("catalogue_updates", "contents_repo_commit")
