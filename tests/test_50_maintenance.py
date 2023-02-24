
import pytest_mock
from psycopg import Connection
import sqlalchemy as sa

from cads_catalogue import database, maintenance


def test_force_vacuum(postgresql: Connection[str], mocker: pytest_mock.MockerFixture) -> None:
    connection_string = (
        f"postgresql+psycopg2://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string, isolation_level="AUTOCOMMIT")
    database.init_database(connection_string)
    conn = engine.connect()
    sql = "SELECT relname FROM pg_stat_all_tables WHERE schemaname = 'public'"
    all_tables = conn.execute(sql).scalars().all()
    spy1 = mocker.spy(sa.engine.Connection, "execute")
    maintenance.force_vacuum(conn)
    effective_args_object_storage_calls = [pm.args for pm in spy1.mock_calls]
    for table in all_tables:
        assert (conn, "VACUUM ANALYZE %s" % table) in effective_args_object_storage_calls
