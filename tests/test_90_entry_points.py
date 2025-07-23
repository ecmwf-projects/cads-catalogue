import datetime
import os.path
import unittest.mock
from typing import Any, Dict, List, Tuple

import pytest
import pytest_mock
import sqlalchemy as sa
import sqlalchemy_utils
from psycopg import Connection
from typer.testing import CliRunner

import alembic.config
from cads_catalogue import (
    contents,
    database,
    entry_points,
    licence_manager,
    manager,
    messages,
    repos,
    utils,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_RESOURCES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-forms-json")
TEST_MESSAGES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-messages")
TEST_LICENCES_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-licences")
TEST_CIM_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-forms-cim-json")
TEST_CONTENTS_DATA_PATH = os.path.join(TESTDATA_PATH, "cads-contents-json")

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
                "cads-contents-json",
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
            "download_filename": "https://www.spdx.org/licenses/eumetsat.html",
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
    _git_repo = mocker.patch(
        "cads_catalogue.repos.get_repo_url", return_value="a_repo_url"
    )
    mocker.patch("cads_catalogue.object_storage.test_connection")
    folder_commit_hashes = (
        "e5658fef07333700272e36a43df0628efacb5f04",
        "5f662d202e4084dd569567bab0957c8a56f79c0f",
        "f0591ec408b59d32a46a5d08b9786641dffe5c7e",
        "ebdb3b017a14a42fb75ea7b44992f3f178aa0d69",
        "3ae7a244a0f480e90fbcd3eb5e37742614fa3e9b",
        "a0ae2002dec8b4b8b0ba8f2b5223722a71d84b8d",
    )
    mocker.patch.object(
        repos, "get_last_commit_hash", new=get_last_commit_factory(folder_commit_hashes)
    )
    mocker.patch.object(alembic.config, "main")
    _create_database = mocker.spy(sqlalchemy_utils, "create_database")
    _init_database = mocker.spy(database, "init_database")
    _load_licences_from_folder = mocker.spy(
        licence_manager, "load_licences_from_folder"
    )
    _update_catalogue_contents = mocker.spy(contents, "update_catalogue_contents")
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--exclude-resources",
            "--exclude-messages",
            "--exclude-contents",
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
    # check load of contents is not run
    _update_catalogue_contents.assert_not_called()
    _update_catalogue_contents.reset_mock()
    # check object storage calls
    assert (
        _store_file.call_count == 7
    )  # num.licences * 2 - 1 (a download_filename is an external url) = 7

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
            session.execute(sa.text("select count(*) from contents")).scalars().one()
            == 0
        )
        assert (
            session.execute(sa.text("select count(*) from resources")).scalars().one()
            == 0
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit, content_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                "e5658fef07333700272e36a43df0628efacb5f04",
                {},
                "f0591ec408b59d32a46a5d08b9786641dffe5c7e",
                None,
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--exclude-resources",
            "--exclude-messages",
            "--exclude-contents",
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
    # check load of contents is not run
    _update_catalogue_contents.assert_not_called()
    _update_catalogue_contents.reset_mock()
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--exclude-resources",
            "--exclude-licences",
            "--exclude-contents",
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
    # check load of contents is not run
    _update_catalogue_contents.assert_not_called()
    _update_catalogue_contents.reset_mock()
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
        assert (
            session.execute(sa.text("select count(*) from contents")).scalars().one()
            == 0
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                {},
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
                "message_uid": "sites/cds/2023/Jan/2021-01-example-of-info-active.md",
                "site": "cds",
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
                "message_uid": "sites/cds/2023/Jan/2023-01-example-of-archived-critical.md",
                "site": "cds",
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
                "message_uid": "sites/cds/2023/Jan/2023-01-example-warning-active.md",
                "site": "cds",
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
                "message_uid": "sites/ads/2023/02/2021-02-example-of-info-active.md",
                "site": "ads",
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
                "message_uid": "sites/ads/2023/02/2023-02-example-of-archived-critical.md",
                "site": "ads",
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
                "message_uid": "sites/ads/2023/02/2023-02-example-warning-active.md",
                "site": "ads",
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

    # 3. load only a dataset (including licences, messages, contents) --------------------------
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--include",
            "reanalysis-era5-land",
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config.yaml"),
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
    # check load of contents is run only 1 time
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check load of messages is run (because of loading of resources)
    _update_catalogue_messages.assert_called_once()
    _update_catalogue_messages.reset_mock()
    # check object storage calls
    assert _store_file.call_count == 9
    #     # overview.png * 3 = 3 (one from contents)
    #     # layout.json * 4 = 4 (3 from contents)
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
        unittest.mock.call(
            os.path.join(
                TESTDATA_PATH,
                "cads-contents-json",
                "copernicus-interactive-climates-atlas",
                "cica-overview.png",
            ),
            object_storage_url,
            bucket_name=bucket_name,
            subpath="contents/cds/application/copernicus-interactive-climates-atlas",
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
                {},
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
            )
        ]
        sql2 = "select slug, title, site, type from contents order by site, type, slug"
        assert sorted(session.execute(sa.text(sql2)).all()) == [
            (
                "copernicus-interactive-climates-atlas",
                "Copernicus Interactive Climate Atlas",
                "cds",
                "application",
            ),
            ("how-to-api", "CDSAPI setup", "ads", "page"),
            ("how-to-api", "CDSAPI setup", "cds", "page"),
            ("how-to-api-templated", "ADS API setup", "ads", "page"),
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--include",
            "reanalysis-era5-land",
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config.yaml"),
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
    # check load of contents is run (git hash not changed but a resource is processed)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage called for contents
    _store_file.call_count == 4
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
            == 1
        )
        assert (
            session.execute(sa.text("select count(*) from contents")).scalars().one()
            == 4
        )
        sql = (
            "select catalogue_repo_commit, metadata_repo_commit, licence_repo_commit, "
            "message_repo_commit, cim_repo_commit, content_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                {},
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
                folder_commit_hashes[5],
            )
        ]

    # 4. change a licence, a message and a content and repeat last run with force = True -----------
    with session_obj() as session:
        session.execute(
            sa.text(
                "update licences set title='a new title' where licence_uid='eumetsat-cm-saf'"
            )
        )
        session.execute(
            sa.text(
                "update messages set live=false "
                "where message_uid='sites/c3s/2023/Jan/2021-01-example-of-info-active.md'"
            )
        )
        session.execute(
            sa.text(
                "update contents set title='a new title' "
                "where slug='how-to-api' and site='ads' and type='page'"
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--include",
            "reanalysis-era5-land",
            "--force",
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config.yaml"),
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
    # check load of contents is run (it's forced)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage called for 1 dataset, 4 licences and 4 contents (5 + 4*2 + 4) - 1 (external URL)
    assert _store_file.call_count == 16
    _store_file.reset_mock()

    # check db changes are reset
    with session_obj() as session:
        assert session.execute(
            sa.text("select title from licences where licence_uid='eumetsat-cm-saf'")
        ).all() == [("EUMETSAT CM SAF products licence",)]
        assert session.execute(
            sa.text(
                "select live from messages "
                "where message_uid='sites/cds/2023/Jan/2021-01-example-of-info-active.md'"
            )
        ).all() == [(True,)]
        assert session.execute(
            sa.text(
                "select title from contents where slug='how-to-api' and site='ads' and type='page'"
            )
        ).all() == [("CDSAPI setup",)]

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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--include",
            "not-existing-*-dataset",
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config.yaml"),
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
    # check load of contents  is run (resources are processed)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage is run (by contents)
    _store_file._store_file.call_count == 4
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--exclude",
            "reanalysis-era5-single-*",
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config.yaml"),
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
    # check load of contents is not run (git hash stable)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage called
    assert _store_file.call_count == 34
    #     # num.datasets overview.png * 2 = 12
    #     # num.datasets layout.json = 6
    #     # num.datasets form.json = 6
    #     # num.datasets constraints.json = 6
    #     # num.contents = 4
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
            "message_repo_commit, cim_repo_commit, content_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (
                folder_commit_hashes[0],
                {},
                folder_commit_hashes[2],
                folder_commit_hashes[3],
                None,
                folder_commit_hashes[5],
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config2.yaml"),
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
    # check load of contents is run (contents config is changed)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage called
    assert _store_file.call_count == 9
    #     # num.datasets overview.png * 2 = 2
    #     # num.datasets layout.json = 1
    #     # num.datasets form.json = 1
    #     # num.datasets constraints.json = 1
    #     # num. contents = 4
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
            "message_repo_commit, cim_repo_commit, content_repo_commit from catalogue_updates"
        )
        assert session.execute(sa.text(sql)).all() == [
            (folder_commit_hashes[0], {"a_repo_url": folder_commit_hashes[1]})
            + folder_commit_hashes[2:]
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
            ("reanalysis-era5-pressure-levels", "reanalysis-era5-single-levels"),
            ("reanalysis-era5-single-levels", "reanalysis-era5-pressure-levels"),
        ]
        sql = "select site, title, slug, type, description from contents order by title, site"
        assert session.execute(sa.text(sql)).all() == [
            (
                "ads",
                "ADS2 API setup",
                "how-to-api-templated",
                "page",
                "Access 33 items of ADS Data Store catalogue, with search and availability features",
            ),
            (
                "ads",
                "CDSAPI setup",
                "how-to-api",
                "page",
                "Access the full data store catalogue, with search and availability features",
            ),
            (
                "cds",
                "CDSAPI setup",
                "how-to-api",
                "page",
                "Access the full data store catalogue, with search and availability features",
            ),
            (
                "cds",
                "Copernicus Interactive Climate Atlas",
                "copernicus-interactive-climates-atlas",
                "application",
                "The Copernicus Interactive Climate Atlas provides graphical "
                "information about recent past trends and future changes "
                "(for different scenarios and global warming levels)",
            ),
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config2.yaml"),
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
    # check load of contents is not run (git hash stable)
    _update_catalogue_contents.assert_not_called()
    _update_catalogue_contents.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()
    _store_file.reset_mock()

    # 9. change a dataset and run again with force ---------------------------------------
    with session_obj() as session:
        session.execute(
            sa.text(
                "update resources set title='a new title', "
                'sanity_check=\'{"name": "my-name", "tags": ["tag1", "tag2"]}\' '
                "where resource_uid='reanalysis-era5-land'"
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--force",
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config2.yaml"),
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
    # check load of contents is run (force)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage called
    assert _store_file.call_count == 51
    #     # num.licences * 2 = 8
    #     # num.datasets overview.png * 2 = 16
    #     # num.datasets layout.json = 8
    #     # num.datasets form.json = 8
    #     # num.datasets constraints.json = 8
    #     # num.contents = 4
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config2.yaml"),
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
    # check load of contents is not run (git hash stable)
    _update_catalogue_contents.assert_not_called()
    _update_catalogue_contents.reset_mock()
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--overrides-path",
            os.path.join(TESTDATA_PATH, "override2.yaml"),
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config2.yaml"),
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
    # check load of contents is run (force)
    _update_catalogue_contents.assert_called_once()
    _update_catalogue_contents.reset_mock()
    # check object storage called
    assert _store_file.call_count == 51
    #     # num.licences * 2 = 8
    #     # num.datasets overview.png * 2 = 16
    #     # num.datasets layout.json = 8
    #     # num.datasets form.json = 8
    #     # num.datasets constraints.json = 8
    #     # num.contents = 4
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
            "--overrides-path",
            os.path.join(TESTDATA_PATH, "override2.yaml"),
            "--contents-config-path",
            os.path.join(TEST_CONTENTS_DATA_PATH, "template_config2.yaml"),
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
    # check load of contents is not run (git hash stable)
    _update_catalogue_contents.assert_not_called()
    _update_catalogue_contents.reset_mock()
    # check object storage not called
    _store_file.assert_not_called()
    _store_file.reset_mock()


def test_update_sanity_check(
    caplog: pytest.LogCaptureFixture,
    postgresql: Connection[str],
    mocker: pytest_mock.MockerFixture,
) -> None:
    # just prepare filling the database
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    sqlalchemy_utils.drop_database(connection_string)
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)
    object_storage_url = "http://myobject-storage:myport/"
    doc_storage_url = "http://mypublic-storage/"
    bucket_name = "my_bucket"
    object_storage_kws: dict[str, Any] = {
        "aws_access_key_id": "storage_user",
        "aws_secret_access_key": "storage_password",
    }
    _store_file = mocker.patch(
        "cads_catalogue.object_storage.store_file", return_value="an url"
    )
    _git_repo = mocker.patch(
        "cads_catalogue.repos.get_repo_url", return_value="a_repo_url"
    )
    mocker.patch("cads_catalogue.object_storage.test_connection")
    folder_commit_hashes = (
        "e5658fef07333700272e36a43df0628efacb5f04",
        "5f662d202e4084dd569567bab0957c8a56f79c0f",
        "f0591ec408b59d32a46a5d08b9786641dffe5c7e",
        "ebdb3b017a14a42fb75ea7b44992f3f178aa0d69",
        "3ae7a244a0f480e90fbcd3eb5e37742614fa3e9b",
        "a0ae2002dec8b4b8b0ba8f2b5223722a71d84b8d",
    )
    mocker.patch.object(
        repos, "get_last_commit_hash", new=get_last_commit_factory(folder_commit_hashes)
    )
    mocker.patch.object(alembic.config, "main")

    runner.invoke(
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
            "--contents-folder-path",
            TEST_CONTENTS_DATA_PATH,
        ],
        env={
            "OBJECT_STORAGE_URL": object_storage_url,
            "DOCUMENT_STORAGE_URL": doc_storage_url,
            "STORAGE_ADMIN": object_storage_kws["aws_access_key_id"],
            "STORAGE_PASSWORD": object_storage_kws["aws_secret_access_key"],
            "CATALOGUE_BUCKET": bucket_name,
        },
    )

    # running the test with default retain
    report_path = os.path.join(TESTDATA_PATH, "reports.json")
    result = runner.invoke(
        entry_points.app,
        [
            "update-sanity-check",
            report_path,
            "--connection-string",
            connection_string,
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
    # check db content
    expected_db: List[Tuple[str, List[Dict[str, Any]] | None]] = [
        ("cams-global-reanalysis-eac4", None),
        ("cams-global-reanalysis-eac4-monthly", None),
        (
            "derived-near-surface-meteorological-variables",
            [
                {
                    "req_id": "747cd1ec-f74a-469f-90db-a5f123365389",
                    "success": True,
                    "started_at": "2025-03-19T20:22:04.386113+00:00",
                    "finished_at": "2025-03-19T20:22:21.805289+00:00",
                },
                {
                    "req_id": "f6fb3372-23f0-49b4-afe7-f8bd2341aa88",
                    "success": True,
                    "started_at": "2025-03-19T19:17:33.336182+00:00",
                    "finished_at": "2025-03-19T19:17:40.393194+00:00",
                },
                {
                    "req_id": "c2a8db72-2e07-48e1-9367-3917fe543a52",
                    "success": True,
                    "started_at": "2025-03-19T18:43:29.388729+00:00",
                    "finished_at": "2025-03-19T18:43:53.651144+00:00",
                },
            ],
        ),
        (
            "reanalysis-era5-land",
            [
                {
                    "req_id": "ad316f3e-b74c-4c32-8c79-5b37ad485a67",
                    "success": True,
                    "started_at": "2025-03-19T19:39:19.873201+00:00",
                    "finished_at": "2025-03-19T19:39:37.786999+00:00",
                },
                {
                    "req_id": "a2dd89b2-671d-46c5-adfd-67f88fd89bd2",
                    "success": True,
                    "started_at": "2025-03-19T18:53:35.274381+00:00",
                    "finished_at": "2025-03-19T18:53:47.088402+00:00",
                },
                {
                    "req_id": "8b2e4f80-4f87-4be6-a15d-1bee49cd00bf",
                    "success": True,
                    "started_at": "2025-03-19T17:00:46.054276+00:00",
                    "finished_at": "2025-03-19T17:01:23.561730+00:00",
                },
            ],
        ),
        (
            "reanalysis-era5-land-monthly-means",
            [
                {
                    "req_id": "679d9ed1-6750-4760-bd48-2c33911d8d13",
                    "success": True,
                    "started_at": "2025-03-19T19:51:36.502811+00:00",
                    "finished_at": "2025-03-19T19:51:44.828018+00:00",
                },
                {
                    "req_id": "700fac07-824e-4884-87a3-88607aa3990c",
                    "success": True,
                    "started_at": "2025-03-19T19:00:48.990793+00:00",
                    "finished_at": "2025-03-19T19:00:56.784068+00:00",
                },
                {
                    "req_id": "2345813e-6214-49b6-b3c7-19d19390db03",
                    "success": True,
                    "started_at": "2025-03-19T17:02:06.425665+00:00",
                    "finished_at": "2025-03-19T17:02:14.207866+00:00",
                },
            ],
        ),
        (
            "reanalysis-era5-pressure-levels",
            [
                {
                    "req_id": "f74112b7-8bca-41e8-bc3d-4251e1c1b68d",
                    "success": True,
                    "started_at": "2025-03-19T19:39:37.789617+00:00",
                    "finished_at": "2025-03-19T19:39:56.825807+00:00",
                },
                {
                    "req_id": "d3a93e9d-4140-43ac-8ac9-2bbf8f71aeb2",
                    "success": True,
                    "started_at": "2025-03-19T18:53:47.089215+00:00",
                    "finished_at": "2025-03-19T18:53:53.507117+00:00",
                },
                {
                    "req_id": "dc985723-f993-400d-bcba-f0481c05853b",
                    "success": True,
                    "started_at": "2025-03-19T17:00:46.025830+00:00",
                    "finished_at": "2025-03-19T17:02:05.591700+00:00",
                },
            ],
        ),
        (
            "reanalysis-era5-single-levels",
            [
                {
                    "req_id": "f3b5914b-49fa-46f7-a6bd-d89fddffdbbb",
                    "success": True,
                    "started_at": "2025-03-19T19:39:56.828625+00:00",
                    "finished_at": "2025-03-19T19:40:15.106225+00:00",
                },
                {
                    "req_id": "92c27e00-80ee-4da7-aedd-31488ac42043",
                    "success": True,
                    "started_at": "2025-03-19T18:53:53.507966+00:00",
                    "finished_at": "2025-03-19T18:54:03.414561+00:00",
                },
                {
                    "req_id": "eeb76ad4-6996-4ecb-a656-066e80aad563",
                    "success": True,
                    "started_at": "2025-03-19T17:00:46.057012+00:00",
                    "finished_at": "2025-03-19T17:02:06.406081+00:00",
                },
            ],
        ),
        (
            "satellite-surface-radiation-budget",
            [
                {
                    "req_id": "fd602e81-b6bd-40a1-bf8d-0e1935af939b",
                    "success": True,
                    "started_at": "2025-03-19T20:05:01.792501+00:00",
                    "finished_at": "2025-03-19T20:05:15.315782+00:00",
                },
                {
                    "req_id": "97d99926-6d5d-4e12-8e36-2eabfa60336c",
                    "success": True,
                    "started_at": "2025-03-19T19:08:29.676061+00:00",
                    "finished_at": "2025-03-19T19:08:39.442759+00:00",
                },
                {
                    "req_id": "8dd93631-90ab-430b-b88a-f993b08853f5",
                    "success": True,
                    "started_at": "2025-03-19T18:30:50.014885+00:00",
                    "finished_at": "2025-03-19T18:30:58.115110+00:00",
                },
            ],
        ),
    ]
    with session_obj() as session:
        effective_db = session.execute(
            sa.select(
                database.Resource.resource_uid, database.Resource.sanity_check
            ).order_by(database.Resource.resource_uid)
        ).all()
        assert effective_db == expected_db

    # running the test with retain=1
    expected_2 = expected_db[:2] + [(d[0], d[1][:1]) for d in expected_db[2:]]  # type: ignore
    report_path = os.path.join(TESTDATA_PATH, "reports.json")
    result = runner.invoke(
        entry_points.app,
        [
            "update-sanity-check",
            report_path,
            "--connection-string",
            connection_string,
            "--retain-only",
            "1",
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
    with session_obj() as session:
        effective_db = session.execute(
            sa.select(
                database.Resource.resource_uid, database.Resource.sanity_check
            ).order_by(database.Resource.resource_uid)
        ).all()
        assert effective_db == expected_2

    # running the test with retain=-1
    expected_3 = expected_db[:2] + [(d[0], [d[1][0]] + d[1]) for d in expected_db[2:]]  # type: ignore
    report_path = os.path.join(TESTDATA_PATH, "reports.json")
    result = runner.invoke(
        entry_points.app,
        [
            "update-sanity-check",
            report_path,
            "--connection-string",
            connection_string,
            "--retain-only",
            "-1",
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
    with session_obj() as session:
        effective_db = session.execute(
            sa.select(
                database.Resource.resource_uid, database.Resource.sanity_check
            ).order_by(database.Resource.resource_uid)
        ).all()
        assert effective_db == expected_3
