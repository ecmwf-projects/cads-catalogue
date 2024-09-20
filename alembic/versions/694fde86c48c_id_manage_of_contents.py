"""id manage of contents.

Revision ID: 694fde86c48c
Revises: 59fa8a6b0a81
Create Date: 2024-09-20 09:01:06.015849

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '694fde86c48c'
down_revision = '59fa8a6b0a81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_contents_type", "contents", ["type"])
    op.drop_column("contents", "content_uid")
    op.add_column("contents", sa.Column("slug", sa.String, index=True, nullable=False))
    op.create_unique_constraint("contents_site_slug_type_key", "contents", ["site", "slug", "type"])


def downgrade() -> None:
    op.drop_constraint("contents_site_slug_type_key", "contents")
    op.drop_column("contents", "slug")
    op.add_column("contents", sa.Column("content_uid", sa.String, index=True, unique=True, nullable=False))
    op.drop_index("ix_contents_type", "contents")
