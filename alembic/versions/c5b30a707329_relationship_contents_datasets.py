"""relationship contents-datasets.

Revision ID: c5b30a707329
Revises: 36caa987229e
Create Date: 2025-01-22 15:20:20.823244

"""

import sqlalchemy as sa

import alembic

# revision identifiers, used by Alembic.
revision = "c5b30a707329"
down_revision = "36caa987229e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.create_table(
        "resources_contents",
        sa.Column(
            "content_id",
            sa.Integer,
            sa.ForeignKey("contents.content_id"),
            primary_key=True,
        ),
        sa.Column(
            "resource_id",
            sa.Integer,
            sa.ForeignKey("resources.resource_id"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    alembic.op.drop_table("resources_contents")
