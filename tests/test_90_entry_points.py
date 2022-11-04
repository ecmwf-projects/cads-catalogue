import datetime
import json
import os.path
import unittest.mock
from typing import Any

import sqlalchemy as sa
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
    tested_datasets = entry_points.DATASETS
    # run the script to load test data
    result = runner.invoke(
        entry_points.app,
        ["setup-test-database", "--connection-string", connection_string],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "STORAGE_ADMIN": object_storage_kws["access_key"],
            "STORAGE_PASSWORD": object_storage_kws["secret_key"],
        },
    )
    assert patch.call_count == 33
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
    kwargs = dict()
    for dataset in tested_datasets:
        for filename in [
            "form.json",
            "overview.png",
            "constraints.json",
            "citation.html",
            "mapping.json",
        ]:
            file_path = os.path.join(TESTDATA_PATH, dataset, filename)
            kwargs = object_storage_kws.copy()
            kwargs["subpath"] = "resources/%s" % dataset
            if (
                dataset
                in (
                    "derived-near-surface-meteorological-variables",
                    "reanalysis-era5-pressure-levels",
                    "reanalysis-era5-single-levels",
                )
                and filename == "overview.png"
            ):
                file_path = os.path.join(TESTDATA_PATH, dataset, "overview.jpg")
            if (
                dataset in ("derived-near-surface-meteorological-variables",)
                and filename == "citation.html"
            ):
                file_path = os.path.join(TESTDATA_PATH, dataset, "citation.md")
            if (
                dataset in ("cams-global-reanalysis-eac4-monthly",)
                and filename == "citation.html"
            ):
                continue
            expected_call = unittest.mock.call(
                file_path, object_storage_url, force=True, **kwargs
            )
            assert expected_call in patch.mock_calls
    for dataset in [
        "reanalysis-era5-pressure-levels",
        "reanalysis-era5-single-levels",
        "derived-near-surface-meteorological-variables",
    ]:
        kwargs["subpath"] = "resources/%s" % dataset
        kwargs["force"] = True
        expected_call = unittest.mock.call(
            os.path.join(TESTDATA_PATH, dataset, "acknowledgement.html"),
            object_storage_url,
            **kwargs,
        )
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
    session.close()
    # reset globals for tests following
    config.dbsettings = None
