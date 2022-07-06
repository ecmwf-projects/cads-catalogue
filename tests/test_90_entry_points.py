import os.path
import subprocess
from pathlib import Path

from psycopg import Connection
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from cads_catalogue import entry_points, manager

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
runner = CliRunner()


def test_load_test_data(
    postgresql: Connection[str], session_obj: sessionmaker, tmp_path: Path
) -> None:
    # load db from test data and dump loaded database in a file
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    manager.store_licences(session_obj, licences, tmp_path)
    datasets = [
        "reanalysis-era5-land-monthly-means",
        "reanalysis-era5-pressure-levels",
    ]
    session = session_obj()
    for dataset in datasets:
        resource_folder_path = os.path.join(TESTDATA_PATH, dataset)
        resource = manager.load_resource_from_folder(resource_folder_path)
        manager.store_dataset(session_obj, resource, tmp_path)
    session.close()
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    expected_dump_path = tmp_path / "expected_dump.sql"
    with open(expected_dump_path, "w") as dumped_file:
        ret = subprocess.call(["pg_dump", connection_string], stdout=dumped_file)
        assert ret == 0
        assert os.path.exists(expected_dump_path)

    # run the script to load test data, dump again and check the dumped file
    runner.invoke(entry_points.app, ["init_db", connection_string])
    effective_dump_path = tmp_path / "effective_dump.sql"
    result = runner.invoke(
        entry_points.app,
        ["load-test-data", connection_string],
        env={"DOCUMENT_STORAGE": str(tmp_path)},
    )
    assert result.exit_code == 0
    with open(effective_dump_path, "w") as dumped_file:
        ret = subprocess.call(["pg_dump", connection_string], stdout=dumped_file)
        assert ret == 0
        assert os.path.exists(effective_dump_path)

    with open(effective_dump_path) as effective_file:
        effective_dump_text = effective_file.read()
    with open(effective_dump_path) as expected_file:
        expected_dump_text = expected_file.read()
    assert expected_dump_text == effective_dump_text

    assert os.path.exists(
        os.path.join(
            tmp_path,
            "licences",
            "licence-to-use-copernicus-products",
            "licence-to-use-copernicus-products.pdf",
        )
    )
    for dataset in [
        "reanalysis-era5-land-monthly-means",
        "reanalysis-era5-pressure-levels",
    ]:
        for filename in ["constraints.json", "form.json"]:
            assert os.path.exists(
                os.path.join(tmp_path, "resources", dataset, filename)
            )

    # import shutil
    # shutil.copy(effective_dump_path, os.path.join(TESTDATA_PATH, "testdb.sql"))
