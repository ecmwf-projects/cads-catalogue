"""add table resource_data

Revision ID: 6a53ad750543
Revises: 4947a1be081e
Create Date: 2023-10-31 08:42:25.681640

"""

import sqlalchemy as sa
import alembic
from sqlalchemy.dialects import postgresql as dialect_postgresql

# revision identifiers, used by Alembic.
revision = '6a53ad750543'
down_revision = '4947a1be081e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    alembic.op.drop_column("resources", "adaptor_configuration")
    alembic.op.drop_column("resources", "constraints_data")
    alembic.op.drop_column("resources", "form_data")
    alembic.op.drop_column("resources", "mapping")
    alembic.op.create_table(
        "resource_data",
        sa.Column("resource_data_id", sa.Integer, primary_key=True),
        sa.Column("adaptor_configuration", dialect_postgresql.JSONB),
        sa.Column("constraints_data", dialect_postgresql.JSONB),
        sa.Column("form_data", dialect_postgresql.JSONB),
        sa.Column("mapping", dialect_postgresql.JSONB),
        sa.Column("resource_uid", sa.String, sa.ForeignKey("resources.resource_uid"), nullable=False)
    )
    alembic.op.create_unique_constraint("resource_uid_uc", "resource_data", ["resource_uid"])


def downgrade() -> None:
    alembic.op.add_column("resources", sa.Column("adaptor_configuration", dialect_postgresql.JSONB))
    alembic.op.add_column("resources", sa.Column("constraints_data", dialect_postgresql.JSONB))
    alembic.op.add_column("resources", sa.Column("form_data", dialect_postgresql.JSONB))
    alembic.op.add_column("resources", sa.Column("mapping", dialect_postgresql.JSONB))
    alembic.op.drop_table("resource_data")
