import pytest_mock
import sqlalchemy as sa
from psycopg import Connection

from cads_catalogue import database
from cads_catalogue.fair import update_fair_score


def test_fair_integration(
    postgresql: Connection[str],
    mocker: pytest_mock.MockerFixture,
) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    database.init_database(connection_string, force=True)
    session_obj = sa.orm.sessionmaker(engine)
    with session_obj() as session:
        res1 = database.Resource(
            resource_id=1,
            resource_uid="res1",
            portal="c3s",
            abstract="Test resource 1",
            description="This is a test resource",
            title="Test Resource 1",
            type="dataset",
            resource_data=database.ResourceData(form_data={}),
        )
        session.add(res1)
        session.commit()
        session.close()

    # New independent session
    session_obj = sa.orm.sessionmaker(engine)
    mocker.patch("cads_catalogue.fair.call_fair_checker", return_value={"foo": "bar"})

    with session_obj() as session:
        update_fair_score(session, "localhost:5000")

        session.query(database.Resource).all()
        res1 = session.query(database.Resource).one()
        res1_data = session.query(database.ResourceData).one()

        assert res1.resource_uid == "res1"
        assert res1.fair_timestamp is not None
        assert res1_data.fair_data == {"foo": "bar"}
