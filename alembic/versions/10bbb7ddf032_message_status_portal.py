"""message -status +portal.

Revision ID: 10bbb7ddf032
Revises: 8ccbe515155c
Create Date: 2023-06-06 15:04:13.173946

"""

import sqlalchemy as sa

import alembic

# revision identifiers, used by Alembic.
revision = "10bbb7ddf032"
down_revision = "8ccbe515155c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.add_column("messages", sa.Column("portal", sa.String, index=True))
    alembic.op.drop_column("messages", "status")


def downgrade() -> None:
    alembic.op.drop_column("messages", "portal")
    sql1 = "CREATE TYPE msg_status AS ENUM ('ongoing', 'closed', 'fixed')"
    sql2 = "ALTER TABLE messages ADD COLUMN status msg_status'"
    for sql in [sql1, sql2]:
        alembic.op.execute(sql)
