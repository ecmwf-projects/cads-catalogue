"""add views for multisite.

Revision ID: fe3054fbc892
Revises: ccdb8e308d41
Create Date: 2023-08-10 12:57:35.547938

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "fe3054fbc892"
down_revision = "ccdb8e308d41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql1 = """
    CREATE VIEW c3s_resources AS
    SELECT * FROM resources
    WHERE portal = 'c3s'
    """
    op.execute(sql1)
    sql2 = """
    CREATE VIEW cams_resources AS
    SELECT * FROM resources
    WHERE portal = 'cams'
    """
    op.execute(sql2)


def downgrade() -> None:
    op.execute("DROP VIEW c3s_resources")
    op.execute("DROP VIEW cams_resources")
