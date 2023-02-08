import os.path
import unittest.mock
from typing import Any

import pytest
import pytest_mock
import sqlalchemy as sa
import sqlalchemy_utils
from psycopg import Connection
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from cads_catalogue import config, database, entry_points, manager, utils

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


def test_setup_database(
    postgresql: Connection[str], mocker: pytest_mock.MockerFixture
) -> None:
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
    doc_storage_url = "http://mypublic-storage/"
    bucket_name = "my_bucket"
    object_storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    expected_licences = [
        {
            "licence_id": 1,
            "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
            "revision": 4,
            "title": "CCI product licence",
            "download_filename": "an url",
        },
        {
            "licence_id": 2,
            "licence_uid": "eumetsat-cm-saf",
            "revision": 1,
            "title": "EUMETSAT CM SAF products licence",
            "download_filename": "an url",
        },
        {
            "licence_id": 3,
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
            "download_filename": "an url",
        },
    ]
    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    # run the script to load test data
    result = runner.invoke(
        entry_points.app,
        ["setup-database", "--connection-string", connection_string, "--force"],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    # check no errors
    assert result.exit_code == 0
    assert (
        patch.call_count == 42
    )  # len(licences)+len(OBJECT_STORAGE_UPLOAD_FILES)*len(resources)
    # store of pdf of licence
    assert (licence_path, object_storage_url) in [mp.args for mp in patch.mock_calls]
    assert {
        "bucket_name": bucket_name,
        "force": True,
        "subpath": "licences/licence-to-use-copernicus-products",
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    } in [mp.kwargs for mp in patch.mock_calls]
    # check object storage calls
    expected_calls = [  # these are only some
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH, "cds-licences", "licence-to-use-copernicus-products.pdf"
            ),
            object_storage_url,
            bucket_name=bucket_name,
            force=True,
            subpath="licences/licence-to-use-copernicus-products",
            **object_storage_kws,
        ),
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH,
                "cads-forms-json",
                "reanalysis-era5-land",
                "overview.png",
            ),
            object_storage_url,
            bucket_name=bucket_name,
            force=True,
            subpath="resources/reanalysis-era5-land",
            **object_storage_kws,
        ),
    ]
    for expected_call in expected_calls:
        assert expected_call in patch.mock_calls

    # check db content
    session = session_obj()
    resources = session.query(database.Resource).order_by(
        database.Resource.resource_uid
    )

    utils.compare_resources_with_dumped_file(
        resources, os.path.join(TESTDATA_PATH, "dumped_resources.txt")
    )

    licences = [
        utils.object_as_dict(ll) for ll in session.query(database.Licence).all()
    ]
    assert len(licences) == len(expected_licences)
    for expected_licence in expected_licences:
        effective_found = (
            session.query(database.Licence)
            .filter_by(licence_uid=expected_licence["licence_uid"])
            .all()
        )
        assert effective_found
        for field in ["revision", "title", "download_filename"]:
            assert getattr(effective_found[0], field) == expected_licence[field]

    resl = (
        session.query(database.Resource)
        .filter_by(resource_uid="reanalysis-era5-single-levels")
        .one()
    )
    assert resl.related_resources[0].resource_uid == "reanalysis-era5-pressure-levels"

    session.close()

    result = runner.invoke(
        entry_points.app,
        ["setup-database", "--connection-string", connection_string, "--force"],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    assert result.exit_code == 0

    # reset globals for tests following
    config.dbsettings = None


def test_transaction_setup_database(
    caplog: pytest.LogCaptureFixture,
    postgresql: Connection[str],
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Here we want to test that transactions are managed outside the setup test database."""
    connection_string = (
        f"postgresql+psycopg2://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    object_storage_url = "http://myobject-storage:myport/"
    doc_storage_url = "http://mypublic-storage/"
    bucket_name = "my_bucket"
    object_storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    # create the db empty
    engine = database.init_database(connection_string)
    # add some dummy data
    engine.execute(
        "INSERT INTO licences (licence_uid, revision, title, download_filename) "
        "VALUES ('a-licence', 1, 'a licence', 'a file.pdf')"
    )
    engine.execute(
        "INSERT INTO resources (resource_uid, abstract, description, type) "
        "VALUES ('dummy-dataset', 'a dummy ds', '[]', 'dataset')"
    )
    session_obj = sessionmaker(engine)
    # simulate the object storage working...
    mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    # ... but impose the store_dataset fails to work...
    mocker.patch.object(
        manager, "resource_sync", side_effect=Exception("dataset error")
    )
    # ....so the entry point execution should fail...
    result = runner.invoke(
        entry_points.app,
        ["setup-database", "--connection-string", connection_string, "--force"],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    # ...without raising any
    assert result.exit_code == 0
    # ...but there is an error log for each dataset
    error_messages = [r.msg for r in caplog.records if r.levelname == "ERROR"]
    for dataset_name in os.listdir(os.path.join(TESTDATA_PATH, "cads-forms-json")):
        assert len([e for e in error_messages if dataset_name in e]) >= 1
    # ...anyway the licence content is updated...
    with session_obj() as session:
        licences = session.execute(
            "select licence_uid from licences order by lower(licence_uid)"
        ).all()
        assert licences == [
            ("a-licence",),
            ("CCI-data-policy-for-satellite-surface-radiation-budget",),
            ("eumetsat-cm-saf",),
            ("licence-to-use-copernicus-products",),
        ]
        #  ....but the resources must stay unchanged
        resources = session.execute(
            "select resource_uid, abstract, description, type from resources"
        ).all()
        assert resources == [("dummy-dataset", "a dummy ds", [], "dataset")]
    session.close()
