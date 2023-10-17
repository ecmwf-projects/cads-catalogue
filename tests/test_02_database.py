from typing import Any

import sqlalchemy as sa
from psycopg import Connection
from sqlalchemy.orm import sessionmaker

from cads_catalogue import config, database


def test_init_database(postgresql: Connection[str]) -> None:
    connection_string = (
        f"postgresql+psycopg2://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    conn = engine.connect()
    query = sa.text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )
    expected_tables_at_beginning: set[str] = set()
    expected_tables_complete = set(database.metadata.tables).union({"alembic_version"})
    assert set(conn.execute(query).scalars()) == expected_tables_at_beginning  # type: ignore

    database.init_database(connection_string, force=True)
    assert set(conn.execute(query).scalars()) == expected_tables_complete  # type: ignore
    conn.close()


def test_ensure_session_obj(postgresql: Connection[str], temp_environ: Any) -> None:
    temp_environ["catalogue_db_host"] = "cataloguehost"
    temp_environ["catalogue_db_password"] = postgresql.info.password
    temp_environ["catalogue_db_user"] = "user"
    temp_environ["catalogue_db_host_read"] = "read_only_host"
    temp_environ["catalogue_db_name"] = "catalogue"
    ret_value = database.ensure_session_obj()
    assert isinstance(ret_value, sessionmaker)
    assert (
        str(ret_value.kw["bind"].url) == "postgresql://user:***@cataloguehost/catalogue"
    )

    config.dbsettings = None
    ret_value = database.ensure_session_obj(read_only=True)
    assert isinstance(ret_value, sessionmaker)
    assert (
        str(ret_value.kw["bind"].url)
        == "postgresql://user:***@read_only_host/catalogue"
    )
    config.dbsettings = None
