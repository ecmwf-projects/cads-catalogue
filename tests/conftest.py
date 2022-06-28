from typing import Iterator

import pytest
from psycopg import Connection
from sqlalchemy.engine.base import Connection as sa_connection

from cads_catalogue import database


@pytest.fixture()
def conn(postgresql: Connection[str]) -> Iterator[sa_connection]:
    """Init the test database and return a connection object"""
    connection_string = (
        f"postgresql+psycopg://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = database.init_db(connection_string)
    connection = engine.connect()
    yield connection
    connection.close()
