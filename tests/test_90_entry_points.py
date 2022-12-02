import datetime
import json
import os.path
import unittest.mock
from typing import Any

import sqlalchemy as sa
import sqlalchemy_utils
from psycopg import Connection
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from cads_catalogue import config, database, entry_points, manager

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
runner = CliRunner()


def test_init_db(postgresql: Connection[str]) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    conn = engine.connect()
    query = (
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )
    result = runner.invoke(
        entry_points.app, ["init-db", "--connection-string", connection_string]
    )

    assert result.exit_code == 0
    assert set(conn.execute(query).scalars()) == set(database.metadata.tables)  # type: ignore


def test_setup_test_database(postgresql: Connection[str], mocker) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    sqlalchemy_utils.drop_database(connection_string)
    engine = sa.create_engine(connection_string)
    session_obj = sessionmaker(engine)
    licence_path = os.path.join(
        TESTDATA_PATH, "cds-licences/licence-to-use-copernicus-products.pdf"
    )
    object_storage_url = "http://myobject-storage:myport/"
    object_storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    expected_licences = [
        {
            "download_filename": "an url",
            "licence_id": 1,
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
        }
    ]

    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    # only load basic datasets
    spy_initdb = mocker.spy(database, "init_database")
    # run the script to load test data
    result = runner.invoke(
        entry_points.app,
        ["setup-test-database", "--connection-string", connection_string, "--force"],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
        },
    )
    assert spy_initdb.call_count == 1
    assert patch.call_count == 15
    # store of pdf of licence
    assert patch.mock_calls[0].args == (licence_path, object_storage_url)
    assert patch.mock_calls[0].kwargs == {
        "force": True,
        "subpath": "licences/licence-to-use-copernicus-products",
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }

    # check no errors
    assert result.exit_code == 0
    # check object storage calls
    expected_calls = [  # these are only some
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH, "cds-licences", "licence-to-use-copernicus-products.pdf"
            ),
            object_storage_url,
            force=True,
            subpath="licences/licence-to-use-copernicus-products",
            **object_storage_kws,
        ),
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH,
                "satellite-surface-radiation-budget",
                "json-config",
                "layout.json",
            ),
            object_storage_url,
            force=True,
            subpath="resources/satellite-surface-radiation-budget",
            **object_storage_kws,
        ),
    ]
    for expected_call in expected_calls:
        assert expected_call in patch.mock_calls

    # check db content
    session = session_obj()
    resources = [
        manager.object_as_dict(r)
        for r in session.query(database.Resource).order_by(
            database.Resource.resource_uid
        )
    ]
    # with open(os.path.join(TESTDATA_PATH, 'dumped_resources.txt'), 'w') as fp:
    #     json.dump(resources, fp, default=str, indent=4)
    with open(os.path.join(TESTDATA_PATH, "dumped_resources.txt")) as fp:
        expected_resources: list[dict[str, Any]] = json.load(fp)
    licences = [
        manager.object_as_dict(ll) for ll in session.query(database.Licence).all()
    ]

    assert licences == expected_licences
    for i, resource in enumerate(resources):
        for key in resource:
            if key == "record_update":
                continue
            value = resource[key]
            if isinstance(value, datetime.date):
                value = value.isoformat()
            assert value == expected_resources[i][key]
    res = session.execute(
        "SELECT related_resource_id, parent_resource_id, child_resource_id"
        " FROM related_resources ORDER BY related_resource_id"
    ).all()
    assert res == []
    session.close()

    # spy_initdb.reset_mock()
    # result = runner.invoke(
    #     entry_points.app,
    #     ["setup-test-database", "--connection-string", connection_string],
    #     env={
    #         "OBJECT_STORAGE_URL": object_storage_url,
    #         "STORAGE_ADMIN": object_storage_kws["access_key"],
    #         "STORAGE_PASSWORD": object_storage_kws["secret_key"],
    #     },
    # )
    # assert spy_initdb.call_count == 0
    # assert result.exit_code == 1

    spy_initdb.reset_mock()
    result = runner.invoke(
        entry_points.app,
        ["setup-test-database", "--connection-string", connection_string, "--force"],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
        },
    )
    assert spy_initdb.call_count == 1
    assert result.exit_code == 0

    # reset globals for tests following
    config.dbsettings = None


def test_transaction_setup_test_database(postgresql: Connection[str], mocker) -> None:
    """ "here we want to test that transactions are managed outside the setup test database"""
    connection_string = (
        f"postgresql+psycopg2://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    object_storage_url = "http://myobject-storage:myport/"
    object_storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    sqlalchemy_utils.drop_database(connection_string)
    engine = sa.create_engine(connection_string)
    session_obj = sessionmaker(engine)
    # simulate the object storage working...
    mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    # ... but the store_dataset fails to work
    mocker.patch.object(
        manager, "store_dataset", side_effect=Exception("dataset error")
    )
    # the entry point execution should fail
    result = runner.invoke(
        entry_points.app,
        ["setup-test-database", "--connection-string", connection_string, "--force"],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
        },
    )
    assert result.exit_code != 0
    # but db must stay unchanged (empty)
    session = session_obj()
    assert session.query(database.Resource).all() == []
    assert session.query(database.Licence).all() == []
    session.close()
