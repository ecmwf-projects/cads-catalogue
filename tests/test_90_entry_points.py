import datetime
import json
import os.path
from pathlib import Path

import sqlalchemy as sa
from psycopg import Connection
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from cads_catalogue import database, entry_points, manager

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


def test_setup_test_database(postgresql: Connection[str], tmp_path: Path) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    session_obj = sessionmaker(engine)
    expected_licences = [
        {
            "download_filename": (
                "licences/licence-to-use-copernicus-products/"
                "licence-to-use-copernicus-products.pdf"
            ),
            "licence_id": 1,
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
        }
    ]
    # run the script to load test data
    result = runner.invoke(
        entry_points.app,
        ["setup-test-database", "--connection-string", connection_string],
        env={"DOCUMENT_STORAGE": str(tmp_path)},
    )
    # check no errors
    assert result.exit_code == 0
    # check document storage
    for dataset in [
        "reanalysis-era5-land-monthly-means",
        "reanalysis-era5-pressure-levels",
    ]:
        for filename in ["constraints.json", "form.json"]:
            assert os.path.exists(
                os.path.join(tmp_path, "resources", dataset, filename)
            )
    assert os.path.exists(
        os.path.join(
            tmp_path,
            "licences",
            "licence-to-use-copernicus-products",
            "licence-to-use-copernicus-products.pdf",
        )
    )
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
    # expected_resources: list[dict[str, Any]] = []
    with open(os.path.join(TESTDATA_PATH, "dumped_resources.txt")) as fp:
        expected_resources = json.load(fp)
    licences = [
        manager.object_as_dict(ll) for ll in session.query(database.Licence).all()
    ]

    assert licences == expected_licences

    for i, resource in enumerate(resources):
        for key in resource:
            if key in ("record_update",):
                continue
            value = resource[key]
            if isinstance(value, datetime.date):
                value = value.isoformat()
            assert value == expected_resources[i][key]
    session.close()
