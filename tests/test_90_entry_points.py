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
    database,
    entry_points,
    licence_manager,
    manager,
    messages,
    utils,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_RESOURCES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-forms-json")
TEST_MESSAGES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-messages")
TEST_LICENCES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-licences")
TEST_CIM_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-forms-cim-json")

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


def get_last_commit_factory(expected_values):
    def dummy_get_last_commit_hash(folder):
        """Use for testing."""
        for i, repo_name in enumerate(
            [
                "catalogue",
                "cads-forms-json",
                "cads-licences",
                "cads-messages",
                "cads-forms-cim-json",
            ]
        ):
            if repo_name in folder.split(os.path.sep)[-1]:
                return expected_values[i]
        return None

    return dummy_get_last_commit_hash


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
            "portal": None,
            "scope": "dataset",
        },
        {
            "licence_id": 2,
            "licence_uid": "eumetsat-cm-saf",
            "revision": 1,
            "title": "EUMETSAT CM SAF products licence",
            "download_filename": "an url",
            "portal": None,
            "scope": "dataset",
        },
        {
            "licence_id": 3,
            "licence_uid": "data-protection-privacy-statement",
            "revision": 24,
            "title": "Data protection and privacy statement",
            "download_filename": "an url",
            "portal": "c3s",
            "scope": "portal",
        },
        {
            "licence_id": 4,
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
            "download_filename": "an url",
            "portal": None,
            "scope": "dataset",
        },
    ]
    _store_file = mocker.patch(
        "cads_catalogue.object_storage.store_file", return_value="an url"
    )
    folder_commit_hashes = (
        "e5658fef07333700272e36a43df0628efacb5f04",
        "5f662d202e4084dd569567bab0957c8a56f79c0f",
        "f0591ec408b59d32a46a5d08b9786641dffe5c7e",
        "ebdb3b017a14a42fb75ea7b44992f3f178aa0d69",
        "3ae7a244a0f480e90fbcd3eb5e37742614fa3e9b",
    )
    mocker.patch.object(
        utils, "get_last_commit_hash", new=get_last_commit_factory(folder_commit_hashes)
    )
    mocker.patch.object(alembic.config, "main")
    _create_database = mocker.spy(sqlalchemy_utils, "create_database")
    _init_database = mocker.spy(database, "init_database")
    _load_licences_from_folder = mocker.spy(
        licence_manager, "load_licences_from_folder"
    )
    _resource_sync = mocker.spy(manager, "resource_sync")
    _update_catalogue_messages = mocker.spy(messages, "update_catalogue_messages")

    # 1. load only licences -------------------------------------------------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--exclude-resources",
            "--exclude-messages",
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
    _create_database.assert_called_once()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is run
    _load_licences_from_folder.assert_called_once()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is not run
    _update_catalogue_messages.assert_not_called()
    _update_catalogue_messages.reset_mock()
    # check object storage calls
    assert _store_file.call_count == 8  # num.licences * 2 = 8

    # store of pdf of licence
    assert (licence_path, object_storage_url) in [
        mp.args for mp in _store_file.mock_calls
    ]
    assert {
        "bucket_name": bucket_name,
        "subpath": "licences/licence-to-use-copernicus-products",
        "aws_access_key_id": "storage_user",
        "aws_secret_access_key": "storage_password",
    } in [mp.kwargs for mp in _store_file.mock_calls]
    # check object storage calls
    expected_calls = [  # these are only some
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH, "cads-licences", "licence-to-use-copernicus-products.pdf"
            ),
            object_storage_url,
            bucket_name=bucket_name,
            subpath="licences/licence-to-use-copernicus-products",
            **object_storage_kws,
        ),
    ]
    for expected_call in expected_calls:
        assert expected_call in _store_file.mock_calls
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        # licences are not removed: remove orphans is automatic disabled
        assert (
            session.execute(sa.text("select count(*) from licences")).scalars().one()
            == 4
        )

        assert (
            session.execute(sa.text("select count(*) from messages")).scalars().one()
            == 0
        )
        assert (
            session.execute(sa.text("select count(*) from resources")).scalars().one()
            == 0
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                "e5658fef07333700272e36a43df0628efacb5f04",
                None,
                "f0591ec408b59d32a46a5d08b9786641dffe5c7e",
                None,
                None,
            )
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

    # 1.bis: load only licences a second time--------------------------------------------
    # (git hash is the same, no processing)
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--exclude-resources",
            "--exclude-messages",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is run
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is not run
    _update_catalogue_messages.assert_not_called()
    _update_catalogue_messages.reset_mock()
    # check object storage calls
    _store_file.assert_not_called()
    _store_file.reset_mock()

    # 2. load only messages -------------------------------------------------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--exclude-resources",
            "--exclude-licences",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is run
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage calls
    _store_file.assert_not_called()
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        assert (
            session.execute(sa.text("select count(*) from licences")).scalars().one()
            == 4
        )

        assert (
            session.execute(sa.text("select count(*) from messages")).scalars().one()
            == 9
        )
        assert (
            session.execute(sa.text("select count(*) from resources")).scalars().one()
            == 0
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                None,
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
            )
        ]
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
                "entries": [
                    "reanalysis-era5-xxx",
                    "satellite-surface-radiation-budget",
                ],
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
                "entries": [
                    "reanalysis-era5-land",
                    "satellite-surface-radiation-budget",
                ],
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

    # 3. load only a dataset (including licences and messages) --------------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--include",
            "reanalysis-era5-land",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash not changed)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is run only 1 time
    _resource_sync.assert_called_once()
    _resource_sync.reset_mock()
    # check load of messages is run (because of loading of resources)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage calls
    assert _store_file.call_count == 5
    #     # overview.png * 2 = 2
    #     # layout.json = 1
    #     # form.json = 1
    #     # constraints.json = 1
    #     # check object storage calls
    expected_calls = [  # these are only some
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH,
                "cads-forms-json",
                "reanalysis-era5-land",
                "overview.png",
            ),
            object_storage_url,
            bucket_name=bucket_name,
            subpath="resources/reanalysis-era5-land",
            **object_storage_kws,
        ),
    ]
    for expected_call in expected_calls:
        assert expected_call in _store_file.mock_calls
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        resources = session.execute(
            sa.select(database.Resource).order_by(database.Resource.resource_uid)
        ).scalars()
        utils.compare_resources_with_dumped_file(
            resources,
            os.path.join(TESTDATA_PATH, "dumped_resources3.txt"),
            # note: expected sources_hash can be different on some platforms
            exclude_fields=(
                "record_update",
                "resource_id",
                "search_field",
                "sources_hash",
            ),
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                None,
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
            )
        ]

    # 3.bis repeat last run -------------------------------------------------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--include",
            "reanalysis-era5-land",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash not changed)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run (folder hash not changed)
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is run (git hash not changed but a resource is processed)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()

    # check db content
    with session_obj() as session:
        assert (
            session.execute(sa.text("select count(*) from licences")).scalars().one()
            == 4
        )

        assert (
            session.execute(sa.text("select count(*) from messages")).scalars().one()
            == 9
        )
        assert (
            session.execute(sa.text("select count(*) from resources")).scalars().one()
            == 1
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                None,
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
            )
        ]

    # 4. change a licence and a message and repeat last run with force = True -----------
    with session_obj() as session:
        session.execute(
            sa.text(
                "update licences set title='a new title' where licence_uid='eumetsat-cm-saf'"
            )
        )
        session.execute(
            sa.text(
                "update messages set live=false "
                "where message_uid='portals/c3s/2023/Jan/2021-01-example-of-info-active.md'"
            )
        )
        session.commit()
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--include",
            "reanalysis-era5-land",
            "--force",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is run (it's forced)
    _load_licences_from_folder.assert_called_once()
    _load_licences_from_folder.reset_mock()
    # check load of resources is run (it's forced)
    _resource_sync.assert_called_once()
    _resource_sync.reset_mock()
    # check load of messages is run (it's forced)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage called for 1 dataset and 4 licences (5 + 4*2)
    assert _store_file.call_count == 13
    _store_file.reset_mock()

    # check db changes are reset
    with session_obj() as session:
        assert session.execute(
            sa.text("select title from licences where licence_uid='eumetsat-cm-saf'")
        ).all() == [("EUMETSAT CM SAF products licence",)]
        assert session.execute(
            sa.text(
                "select live from messages "
                "where message_uid='portals/c3s/2023/Jan/2021-01-example-of-info-active.md'"
            )
        ).all() == [(True,)]

    # 5. use 'include' with a pattern that doesn't match anything ----------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--include",
            "not-existing-*-dataset",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash stable)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run (no match)
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is run (resources are processed)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()
    _store_file.reset_mock()

    # 6. excluding only one dataset -----------------------------------------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--exclude",
            "reanalysis-era5-single-*",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash stable)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is run: times: total (8) - already loaded (1) - excluded (1)
    assert _resource_sync.call_count == 6
    _resource_sync.reset_mock()
    # check load of messages is run (resources are processed)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage called
    assert _store_file.call_count == 30
    #     # num.datasets overview.png * 2 = 12
    #     # num.datasets layout.json = 6
    #     # num.datasets form.json = 6
    #     # num.datasets constraints.json = 6
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        resources = session.execute(
            sa.select(database.Resource).order_by(database.Resource.resource_uid)
        ).scalars()
        utils.compare_resources_with_dumped_file(
            resources,
            os.path.join(TESTDATA_PATH, "dumped_resources4.txt"),
            # note: expected sources_hash can be different on some platforms
            exclude_fields=(
                "record_update",
                "resource_id",
                "search_field",
                "sources_hash",
            ),
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                None,
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
            )
        ]
        sql = (
            "select r1.resource_uid, r2.resource_uid from related_resources "
            "left join resources as r1 on (parent_resource_id=r1.resource_id) "
            "left join resources as r2 on (child_resource_id=r2.resource_id) "
            "order by r1.resource_uid, r2.resource_uid"
        )
        assert session.execute(sa.text(sql)).all() == [
            ("cams-global-reanalysis-eac4", "cams-global-reanalysis-eac4-monthly"),
            ("cams-global-reanalysis-eac4-monthly", "cams-global-reanalysis-eac4"),
            ("reanalysis-era5-land", "reanalysis-era5-land-monthly-means"),
            ("reanalysis-era5-land-monthly-means", "reanalysis-era5-land"),
        ]

    # 7. run without excluding anything -------------------------------------------------
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash stable)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is run: times: total (8) - already loaded (7)
    assert _resource_sync.call_count == 1
    _resource_sync.reset_mock()
    # check load of messages is run (resources are processed)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage called
    assert _store_file.call_count == 5
    #     # num.datasets overview.png * 2 = 2
    #     # num.datasets layout.json = 1
    #     # num.datasets form.json = 1
    #     # num.datasets constraints.json = 1
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        resources = session.execute(
            sa.select(database.Resource).order_by(database.Resource.resource_uid)
        ).scalars()
        utils.compare_resources_with_dumped_file(
            resources,
            os.path.join(TESTDATA_PATH, "dumped_resources5.txt"),
            # note: expected sources_hash can be different on some platforms
            exclude_fields=(
                "record_update",
                "resource_id",
                "search_field",
                "sources_hash",
            ),
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [folder_commit_hashes]
        sql = (
            "select r1.resource_uid, r2.resource_uid from related_resources "
            "left join resources as r1 on (parent_resource_id=r1.resource_id) "
            "left join resources as r2 on (child_resource_id=r2.resource_id) "
            "order by r1.resource_uid, r2.resource_uid"
        )
        assert session.execute(sa.text(sql)).all() == [
            ("cams-global-reanalysis-eac4", "cams-global-reanalysis-eac4-monthly"),
            ("cams-global-reanalysis-eac4-monthly", "cams-global-reanalysis-eac4"),
            ("reanalysis-era5-land", "reanalysis-era5-land-monthly-means"),
            ("reanalysis-era5-land-monthly-means", "reanalysis-era5-land"),
            ("reanalysis-era5-pressure-levels", "reanalysis-era5-single-levels"),
            ("reanalysis-era5-single-levels", "reanalysis-era5-pressure-levels"),
        ]

    # 8. run again -----------------------------------------------------------------------
    # (all should be skipped)
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash stable)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run (git hash stable)
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is not run (git hash stable)
    _update_catalogue_messages.assert_not_called()
    _update_catalogue_messages.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()
    _store_file.reset_mock()

    # 9. change a dataset and run again with force ---------------------------------------
    with session_obj() as session:
        session.execute(
            sa.text(
                "update resources set title='a new title' where resource_uid='reanalysis-era5-land'"
            )
        )
        session.commit()
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--force",
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is run (force)
    _load_licences_from_folder.assert_called_once()
    _load_licences_from_folder.reset_mock()
    # check load of resources is run (force)
    assert _resource_sync.call_count == 8
    _resource_sync.reset_mock()
    # check load of messages is run (force)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage called
    assert _store_file.call_count == 48
    #     # num.licences * 2 = 8
    #     # num.datasets overview.png * 2 = 16
    #     # num.datasets layout.json = 8
    #     # num.datasets form.json = 8
    #     # num.datasets constraints.json = 8
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        resources = session.execute(
            sa.select(database.Resource).order_by(database.Resource.resource_uid)
        ).scalars()
        utils.compare_resources_with_dumped_file(
            resources,
            os.path.join(TESTDATA_PATH, "dumped_resources6.txt"),
            # note: expected sources_hash can be different on some platforms
            exclude_fields=(
                "record_update",
                "resource_id",
                "search_field",
                "sources_hash",
            ),
        )

    # 10. run again without force------------------------------------------------------------------
    # (all should be skipped)
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash stable)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run (git hash stable)
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is not run (git hash stable)
    _update_catalogue_messages.assert_not_called()
    _update_catalogue_messages.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()
    _store_file.reset_mock()

    # 11. run again with a new override file ------------------------------------------------------------
    # (force mode automatically activated)
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--overrides-path",
            os.path.join(TESTDATA_PATH, "override2.yaml"),
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is run (force)
    _load_licences_from_folder.assert_called_once()
    _load_licences_from_folder.reset_mock()
    # check load of resources is run (force)
    assert _resource_sync.call_count == 8
    _resource_sync.reset_mock()
    # check load of messages is run (force)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage called
    assert _store_file.call_count == 48
    #     # num.licences * 2 = 8
    #     # num.datasets overview.png * 2 = 16
    #     # num.datasets layout.json = 8
    #     # num.datasets form.json = 8
    #     # num.datasets constraints.json = 8
    _store_file.reset_mock()

    # check db content
    with session_obj() as session:
        resources = session.execute(
            sa.select(database.Resource).order_by(database.Resource.resource_uid)
        ).scalars()
        utils.compare_resources_with_dumped_file(
            resources,
            os.path.join(TESTDATA_PATH, "dumped_resources7.txt"),
            # note: expected sources_hash can be different on some platforms
            exclude_fields=(
                "record_update",
                "resource_id",
                "search_field",
                "sources_hash",
            ),
        )

    # 12. run again with the same override file ------------------------------------------------------------
    # (all should be skipped)
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
            "--cim-folder-path",
            TEST_CIM_DATA_PATH,
            "--overrides-path",
            os.path.join(TESTDATA_PATH, "override2.yaml"),
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
    # check db is not created
    _create_database.assert_not_called()
    _create_database.reset_mock()
    # check db structure initialized
    _init_database.assert_called_once()
    _init_database.reset_mock()
    # check load of licences is not run (git hash stable)
    _load_licences_from_folder.assert_not_called()
    _load_licences_from_folder.reset_mock()
    # check load of resources is not run (git hash stable)
    _resource_sync.assert_not_called()
    _resource_sync.reset_mock()
    # check load of messages is not run (git hash stable)
    _update_catalogue_messages.assert_not_called()
    _update_catalogue_messages.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()
    _store_file.reset_mock()
