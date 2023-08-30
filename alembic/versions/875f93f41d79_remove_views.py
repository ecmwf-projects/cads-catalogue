"""remove views.

Revision ID: 875f93f41d79
Revises: fe3054fbc892
Create Date: 2023-08-28 10:29:58.886117

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "875f93f41d79"
down_revision = "fe3054fbc892"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW c3s_resources")
    op.execute("DROP VIEW cams_resources")


def downgrade() -> None:
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
