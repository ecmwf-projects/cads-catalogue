
import pytest

from cads_catalogue import database


@pytest.fixture()
def conn(postgresql):  # type:ignore
    """Init the test database and return a connection object"""
    connection_string = f'postgresql+psycopg2://{postgresql.info.user}:' \
                        f'@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}'
    engine = database.init_db(connection_string)  # type: ignore
    connection = engine.connect()
    yield connection
    connection.close()
