import datetime
import os.path
import unittest.mock
from typing import Any

import pytest
import pytest_mock
import sqlalchemy as sa
import sqlalchemy_utils
from psycopg import Connection
from typer.testing import CliRunner

import alembic.config
from cads_catalogue import (
    config,
    database,
    entry_points,
    licence_manager,
    manager,
    utils,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_RESOURCES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-forms-json")
TEST_MESSAGES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-messages")
TEST_LICENCES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-licences")

runner = CliRunner()


def test_init_db(postgresql: Connection[str]) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    conn = engine.connect()
    query = sa.text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )
    result = runner.invoke(
        entry_points.app,
        ["init-db", "--connection-string", connection_string, "--force"],
    )

    assert result.exit_code == 0
    assert set(conn.execute(query).scalars()) == set(database.metadata.tables).union(
        {"alembic_version"}
    )


def get_last_commit_factory(folder1, commit1, folder2, commit2, else_commit3):
    def dummy_get_last_commit(folder):
        """Use for testing is_db_to_update."""
        if folder1 in folder:
            return commit1
        elif folder2 in folder:
            return commit2
        else:
            return else_commit3

    return dummy_get_last_commit


def test_update_catalogue(
    caplog: pytest.LogCaptureFixture,
    postgresql: Connection[str],
    mocker: pytest_mock.MockerFixture,
) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    sqlalchemy_utils.drop_database(connection_string)
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)
    licence_path = os.path.join(
        TESTDATA_PATH, "cads-licences/licence-to-use-copernicus-products.pdf"
    )
    object_storage_url = "http://myobject-storage:myport/"
    doc_storage_url = "http://mypublic-storage/"
    bucket_name = "my_bucket"
    object_storage_kws: dict[str, Any] = {
        "aws_access_key_id": "storage_user",
        "aws_secret_access_key": "storage_password",
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
        "cads_catalogue.object_storage.store_file", return_value="an url"
    )
    last_commit1 = "5f662d202e4084dd569567bab0957c8a56f79c0f"
    last_commit2 = "f0591ec408b59d32a46a5d08b9786641dffe5c7e"
    last_commit3 = "ebdb3b017a14a42fb75ea7b44992f3f178aa0d69"
    dummy_last_commit_function = get_last_commit_factory(
        "cads-forms-json", last_commit1, "cads-licences", last_commit2, last_commit3
    )
    mocker.patch.object(utils, "get_last_commit_hash", new=dummy_last_commit_function)
    mocker.patch.object(alembic.config, "main")
    spy1 = mocker.spy(sqlalchemy_utils, "create_database")
    spy2 = mocker.spy(database, "init_database")
    spy3 = mocker.spy(licence_manager, "load_licences_from_folder")
    spy4 = mocker.spy(manager, "resource_sync")

    # run the script to create the db, and load initial data
    result = runner.invoke(
        entry_points.app,
        [
            "update-catalogue",
            "--connection-string",
            connection_string,
            "--resources-folder-path",
            TEST_RESOURCES_DATA_PATH,
            "--messages-folder-path",
            TEST_MESSAGES_DATA_PATH,
            "--licences-folder-path",
            TEST_LICENCES_DATA_PATH,
        ],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["aws_access_key_id"],
            "STORAGE_PASSWORD": object_storage_kws["aws_secret_access_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    # check no errors
    assert result.exit_code == 0
    # check db is created
    spy1.assert_called_once()
    spy1.reset_mock()
    # check db structure initialized
    spy2.assert_called_once()
    spy2.reset_mock()
    # check load of licences and resources
    spy3.assert_called_once()
    spy3.reset_mock()
    assert spy4.call_count == 8
    spy4.reset_mock()

    assert patch.call_count == 46
    # num.licences * 2 = 6
    # num.datasets overview.png * 2 = 16
    # num.datasets layout.json = 8
    # num.datasets form.json = 8
    # num.datasets constraints.json = 8

    # store of pdf of licence
    assert (licence_path, object_storage_url) in [mp.args for mp in patch.mock_calls]
    assert {
        "bucket_name": bucket_name,
        "force": True,
        "subpath": "licences/licence-to-use-copernicus-products",
        "aws_access_key_id": "storage_user",
        "aws_secret_access_key": "storage_password",
    } in [mp.kwargs for mp in patch.mock_calls]
    # check object storage calls
    expected_calls = [  # these are only some
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH, "cads-licences", "licence-to-use-copernicus-products.pdf"
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
    with session_obj() as session:
        resources = session.execute(
            sa.select(database.Resource).order_by(database.Resource.resource_uid)
        ).scalars()
        utils.compare_resources_with_dumped_file(
            resources,
            os.path.join(TESTDATA_PATH, "dumped_resources.txt"),
            exclude_fields=("record_update", "resource_id", "search_field"),
        )

    assert (
        session.execute(sa.text("select count(*) from messages")).scalars().one() == 9
    )
    expected_msgs = [
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here. This is the full text "
            "message.",
            "date": datetime.datetime(2021, 1, 14, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "message_uid": "portals/c3s/2023/Jan/2021-01-example-of-info-active.md",
            "portal": "c3s",
            "severity": "info",
            "summary": "a summary of the message",
        },
        {
            "content": "# message main body for archived warning message for some "
            "entries \n"
            " \n"
            "Wider **markdown syntax** allowed here. In this example:\n"
            "* *summary* is missing, so only this main body message is used\n"
            "* *status* is missing (indeed actually is not used yet)",
            "date": datetime.datetime(2023, 1, 11, 11, 27, 13),
            "entries": ["reanalysis-era5-xxx", "satellite-surface-radiation-budget"],
            "is_global": False,
            "live": False,
            "message_uid": "contents/2023/2023-01-archived-warning.md",
            "severity": "warning",
            "summary": None,
        },
        {
            "content": "# message main body for active critical message for some "
            "datasets \n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 12, 11, 27, 13),
            "entries": ["reanalysis-era5-land", "satellite-surface-radiation-budget"],
            "is_global": False,
            "live": True,
            "message_uid": "contents/2023/2023-01-era5-issue-456.md",
            "severity": "critical",
            "summary": "example of active critical content message",
        },
        {
            "content": "# message main body for archived critical message for some "
            "datasets \n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 13, 11, 27, 13),
            "entries": ["reanalysis-era5-land", "satellite-surface-xxx"],
            "is_global": False,
            "live": False,
            "message_uid": "contents/foo-bar/this-will-be-also-taken.md",
            "severity": "critical",
            "summary": "example of expired critical content message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 15, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": False,
            "message_uid": "portals/c3s/2023/Jan/2023-01-example-of-archived-critical.md",
            "portal": "c3s",
            "severity": "critical",
            "summary": "A **brief description** of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 16, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "message_uid": "portals/c3s/2023/Jan/2023-01-example-warning-active.md",
            "portal": "c3s",
            "severity": "warning",
            "summary": "A **brief description** of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here. This is the full text "
            "message.",
            "date": datetime.datetime(2023, 2, 14, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "message_uid": "portals/ads/2023/02/2021-02-example-of-info-active.md",
            "portal": "ads",
            "severity": "info",
            "summary": "a summary of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 2, 15, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": False,
            "message_uid": "portals/ads/2023/02/2023-02-example-of-archived-critical.md",
            "portal": "ads",
            "severity": "critical",
            "summary": "A **brief description** of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 2, 16, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "message_uid": "portals/ads/2023/02/2023-02-example-warning-active.md",
            "portal": "ads",
            "severity": "warning",
            "summary": "A **brief description** of the message",
        },
    ]
    db_msgs = session.scalars(
        sa.select(database.Message).order_by(database.Message.message_uid)
    ).unique()
    for db_msg in db_msgs:
        msg_dict = utils.object_as_dict(db_msg)
        expected_msg = [
            m for m in expected_msgs if m["message_uid"] == db_msg.message_uid
        ][0]
        for k, v in expected_msg.items():
            if k == "entries":
                continue
            assert msg_dict[k] == expected_msg[k]
    assert sorted(
        [
            r.resource_uid
            for r in session.execute(
                sa.select(database.Message).filter_by(
                    message_uid="contents/2023/2023-01-archived-warning.md"
                )
            )
            .unique()
            .scalar_one()
            .resources
        ]
    ) == [  # type: ignore
        "reanalysis-era5-land",
        "reanalysis-era5-land-monthly-means",
        "reanalysis-era5-pressure-levels",
        "reanalysis-era5-single-levels",
        "satellite-surface-radiation-budget",
    ]

    licences = [
        utils.object_as_dict(ll)
        for ll in session.scalars(sa.select(database.Licence)).all()
    ]
    assert len(licences) == len(expected_licences)
    for expected_licence in expected_licences:
        effective_found = session.scalars(
            sa.select(database.Licence).filter_by(
                licence_uid=expected_licence["licence_uid"]
            )
        ).all()
        assert effective_found
        for field in ["revision", "title", "download_filename"]:
            assert getattr(effective_found[0], field) == expected_licence[field]

    resl = session.execute(
        sa.select(database.Resource).filter_by(
            resource_uid="reanalysis-era5-single-levels"
        )
    ).scalar_one()
    assert resl.related_resources[0].resource_uid == "reanalysis-era5-pressure-levels"
    catalog_updates = session.scalars(sa.select(database.CatalogueUpdate)).all()
    assert len(catalog_updates) == 1
    assert catalog_updates[0].catalogue_repo_commit == last_commit1
    assert catalog_updates[0].licence_repo_commit == last_commit2
    assert catalog_updates[0].message_repo_commit == last_commit3
    update_time1 = catalog_updates[0].update_time
    session.close()

    # run a second time: do not anything, commit hash are the same
    result = runner.invoke(
        entry_points.app,
        [
            "update-catalogue",
            "--connection-string",
            connection_string,
            "--resources-folder-path",
            TEST_RESOURCES_DATA_PATH,
            "--messages-folder-path",
            TEST_MESSAGES_DATA_PATH,
            "--licences-folder-path",
            TEST_LICENCES_DATA_PATH,
        ],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["aws_access_key_id"],
            "STORAGE_PASSWORD": object_storage_kws["aws_secret_access_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    assert result.exit_code == 0
    # check db is not created
    spy1.assert_not_called()
    spy1.reset_mock()
    # check db structure
    spy2.assert_called_once()
    spy2.reset_mock()
    # check no attempt to load licences and resources
    spy3.assert_not_called()
    spy3.reset_mock()
    spy4.assert_not_called()
    spy4.reset_mock()

    # run a third time: force to run
    result = runner.invoke(
        entry_points.app,
        [
            "update-catalogue",
            "--connection-string",
            connection_string,
            "--force",
            "--resources-folder-path",
            TEST_RESOURCES_DATA_PATH,
            "--messages-folder-path",
            TEST_MESSAGES_DATA_PATH,
            "--licences-folder-path",
            TEST_LICENCES_DATA_PATH,
        ],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["aws_access_key_id"],
            "STORAGE_PASSWORD": object_storage_kws["aws_secret_access_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    assert result.exit_code == 0
    # check db is not created
    spy1.assert_not_called()
    spy1.reset_mock()
    # check db structure
    spy2.assert_called_once()
    spy2.reset_mock()
    # check forced load of licences and resources
    spy3.assert_called_once()
    spy3.reset_mock()
    assert spy4.call_count == 8
    spy4.reset_mock()

    # check nothing changes in the db

    with session_obj() as session:
        licences = [
            utils.object_as_dict(ll)
            for ll in session.scalars(sa.select(database.Licence)).all()
        ]
        assert len(licences) == len(expected_licences)
        for expected_licence in expected_licences:
            effective_found = session.scalars(
                sa.select(database.Licence).filter_by(
                    licence_uid=expected_licence["licence_uid"]
                )
            ).all()
            assert effective_found
            for field in ["revision", "title", "download_filename"]:
                assert getattr(effective_found[0], field) == expected_licence[field]

        resl = session.execute(
            sa.select(database.Resource).filter_by(
                resource_uid="reanalysis-era5-single-levels"
            )
        ).scalar_one()
        assert (
            resl.related_resources[0].resource_uid == "reanalysis-era5-pressure-levels"
        )

        catalog_updates = session.scalars(sa.select(database.CatalogueUpdate)).all()
        assert len(catalog_updates) == 1
        assert catalog_updates[0].catalogue_repo_commit == last_commit1  # type: ignore
        assert catalog_updates[0].licence_repo_commit == last_commit2  # type: ignore
        assert catalog_updates[0].update_time > update_time1  # type: ignore

    caplog.clear()

    # reset globals for tests following
    mocker.resetall()
    config.dbsettings = None
    config.storagesettings = None


def test_transaction_update_catalogue(
    caplog: pytest.LogCaptureFixture,
    postgresql: Connection[str],
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Here we want to test that transactions are managed outside the update catalogue script."""
    mocker.patch.object(alembic.config, "main")
    connection_string = (
        f"postgresql+psycopg2://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    object_storage_url = "http://myobject-storage:myport/"
    doc_storage_url = "http://mypublic-storage/"
    bucket_name = "my_bucket"
    object_storage_kws: dict[str, Any] = {
        "aws_access_key_id": "storage_user",
        "aws_secret_access_key": "storage_password",
    }
    # create the db empty
    engine = database.init_database(connection_string, force=True)
    # add some dummy data
    conn = engine.connect()
    conn.execute(
        sa.text(
            "INSERT INTO licences (licence_uid, revision, title, download_filename, md_filename) "
            "VALUES ('a-licence', 1, 'a licence', 'a file.pdf', 'a file.md')"
        )
    )
    conn.execute(
        sa.text(
            "INSERT INTO resources (resource_uid, abstract, description, type) "
            "VALUES ('dummy-dataset', 'a dummy ds', '[]', 'dataset')"
        )
    )
    conn.commit()

    # simulate the object storage working...
    mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value="an url",
    )
    # ... but impose the store_dataset fails to work...
    mocker.patch.object(
        manager, "resource_sync", side_effect=Exception("dataset error")
    )
    # ....so the entry point execution should fail...
    result = runner.invoke(
        entry_points.app,
        [
            "update-catalogue",
            "--connection-string",
            connection_string,
            "--force",
            "--no-delete-orphans",
            "--resources-folder-path",
            TEST_RESOURCES_DATA_PATH,
            "--messages-folder-path",
            TEST_MESSAGES_DATA_PATH,
            "--licences-folder-path",
            TEST_LICENCES_DATA_PATH,
        ],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["aws_access_key_id"],
            "STORAGE_PASSWORD": object_storage_kws["aws_secret_access_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    # ...without raising any
    assert result.exit_code == 0
    # ...but there is an error log for each dataset
    error_messages = [r.msg for r in caplog.records if r.levelname == "ERROR"]
    for dataset_name in os.listdir(os.path.join(TESTDATA_PATH, "cads-forms-json")):
        assert len([e for e in error_messages if dataset_name in e]) >= 1
    session_obj = sa.orm.sessionmaker(engine)
    # ...anyway the licence content is updated...(uninvolved licence is removed)
    with session_obj() as session:
        licences = session.execute(
            sa.text("select licence_uid from licences order by lower(licence_uid)")
        ).all()
        assert licences == [
            ("CCI-data-policy-for-satellite-surface-radiation-budget",),
            ("eumetsat-cm-saf",),
            ("licence-to-use-copernicus-products",),
        ]
        #  ...but the resources must stay unchanged
        resources = session.execute(
            sa.text("select resource_uid, abstract, description, type from resources")
        ).all()
        assert resources == [("dummy-dataset", "a dummy ds", [], "dataset")]

    # run again without the "no-delete-orphans" options: uninvolved datasets should be removed
    result = runner.invoke(
        entry_points.app,
        [
            "update-catalogue",
            "--connection-string",
            connection_string,
            "--force",
            "--resources-folder-path",
            TEST_RESOURCES_DATA_PATH,
            "--messages-folder-path",
            TEST_MESSAGES_DATA_PATH,
            "--licences-folder-path",
            TEST_LICENCES_DATA_PATH,
        ],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["aws_access_key_id"],
            "STORAGE_PASSWORD": object_storage_kws["aws_secret_access_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )
    # ...without raising any
    assert result.exit_code == 0
    # ...but there is an error log for each dataset
    error_messages = [r.msg for r in caplog.records if r.levelname == "ERROR"]
    for dataset_name in os.listdir(os.path.join(TESTDATA_PATH, "cads-forms-json")):
        assert len([e for e in error_messages if dataset_name in e]) >= 1
    session_obj = sa.orm.sessionmaker(engine)
    # ...anyway the licence content is updated...(uninvolved licence is removed)
    with session_obj() as session:
        licences = session.execute(
            sa.text("select licence_uid from licences order by lower(licence_uid)")
        ).all()
        assert licences == [
            ("CCI-data-policy-for-satellite-surface-radiation-budget",),
            ("eumetsat-cm-saf",),
            ("licence-to-use-copernicus-products",),
        ]
        #  ...and the uninvolved resources are removed too
        resources = session.execute(
            sa.text("select resource_uid, abstract, description, type from resources")
        ).all()
        assert resources == []

    # reset globals for tests following
    config.dbsettings = None
    config.storagesettings = None
    mocker.resetall()
