import operator
import os.path
import uuid
from typing import Any

import pytest_mock
import sqlalchemy as sa

from cads_catalogue import config, database, licence_manager, utils

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def mock_dataset(
    resource_uid: str | None = None,
    abstract: str = "abstract",
    description: dict[str, Any] | None = None,
    **kwargs,
) -> database.Resource:
    dataset = database.Resource(
        resource_uid=resource_uid or str(uuid.uuid4()),
        abstract=abstract,
        description=description or dict(),
        type="dataset",
        **kwargs,
    )
    return dataset


def mock_licence(
    licence_uid: str | None = None,
    revision: int = 1,
    title: str = "title",
    download_filename: str = "licence.pdf",
    md_filename: str = "licence.md",
    **kwargs,
) -> database.Licence:
    licence = database.Licence(
        licence_uid=licence_uid or str(uuid.uuid4()),
        revision=revision,
        title=title,
        download_filename=download_filename,
        md_filename=md_filename,
        **kwargs,
    )
    return licence


def test_licence_sync(
    session_obj: sa.orm.sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    licence_uid = "CCI-data-policy-for-satellite-surface-radiation-budget"
    licence_md = {
        "licence_id": 1,
        "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
        "revision": 4,
        "title": "CCI product licence",
        "download_filename": "an url",
        "scope": "dataset",
        "md_filename": "an url",
        "portal": None,
        "spdx_identifier": None,
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value="an url",
    )
    # start without any licence in the db
    with session_obj() as session:
        licence_manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.scalars(sa.select(database.Licence)).all()
        assert len(db_licences) == 1
        assert utils.object_as_dict(db_licences[0]) == licence_md

    assert patch.call_count == 2
    assert (
        os.path.join(
            licences_folder_path,
            "CCI-data-policy-for-satellite-surface-radiation-budget.pdf",
        ),
        storage_settings.object_storage_url,
    ) in [pm.args for pm in patch.mock_calls]

    assert {
        "bucket_name": "mycatalogue_bucket",
        "subpath": "licences/CCI-data-policy-for-satellite-surface-radiation-budget",
        "aws_access_key_id": "admin1",
        "aws_secret_access_key": "secret1",
    } in [pm.kwargs for pm in patch.mock_calls]
    patch.reset_mock()

    # update an existing licence
    updated_licence = [r for r in licences if r["licence_uid"] == licence_uid][0]
    updated_licence["title"] = "CCI product licence UPDATED"
    licence_md2 = {
        "licence_id": 1,
        "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
        "revision": 4,
        "title": "CCI product licence UPDATED",
        "download_filename": "an url",
        "scope": "dataset",
        "md_filename": "an url",
        "portal": None,
        "spdx_identifier": None,
    }
    licences = [updated_licence]
    with session_obj() as session:
        licence_manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.scalars(sa.select(database.Licence)).all()
        assert len(db_licences) == 1
        assert utils.object_as_dict(db_licences[0]) == licence_md2

    # reset globals for tests following
    config.dbsettings = None
    config.storagesettings = None


def test_load_licences_from_folder() -> None:
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    expected_licences = [
        {
            "download_filename": os.path.join(
                licences_folder_path,
                "CCI-data-policy-for-satellite-surface-radiation-budget.pdf",
            ),
            "md_filename": os.path.join(
                licences_folder_path,
                "CCI-data-policy-for-satellite-surface-radiation-budgetv4.md",
            ),
            "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
            "revision": 4,
            "title": "CCI product licence",
            "scope": "dataset",
            "portal": None,
            "spdx_identifier": None,
        },
        {
            "download_filename": os.path.join(
                licences_folder_path,
                "2021_CDS_Privacy Statement_v2.4.pdf",
            ),
            "md_filename": os.path.join(
                licences_folder_path, "data-protection-privacy-statementv24.md"
            ),
            "licence_uid": "data-protection-privacy-statement",
            "revision": 24,
            "title": "Data protection and privacy statement",
            "scope": "portal",
            "portal": "c3s",
            "spdx_identifier": None,
        },
        {
            "download_filename": "https://www.spdx.org/licenses/eumetsat.html",
            "licence_uid": "eumetsat-cm-saf",
            "revision": 1,
            "title": "EUMETSAT CM SAF products licence",
            "scope": "dataset",
            "md_filename": os.path.join(
                licences_folder_path,
                "eumetsat-cm-safv1.md",
            ),
            "portal": None,
            "spdx_identifier": "eumetsat",
        },
        {
            "download_filename": os.path.join(
                licences_folder_path, "licence-to-use-copernicus-products.pdf"
            ),
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
            "scope": "dataset",
            "md_filename": os.path.join(
                licences_folder_path,
                "licence-to-use-copernicus-productsv12.md",
            ),
            "portal": None,
            "spdx_identifier": None,
        },
    ]
    licences = sorted(
        licence_manager.load_licences_from_folder(licences_folder_path),
        key=operator.itemgetter("licence_uid"),
    )

    assert licences == expected_licences


def test_update_catalogue_licences(
    session_obj: sa.orm.sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    # load and add some licences into the db
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    _ = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value="an url",
    )
    with session_obj() as session:
        licence_attrs = licence_manager.update_catalogue_licences(
            session, licences_folder_path, storage_settings
        )
        assert sorted(licence_attrs) == [
            ("CCI-data-policy-for-satellite-surface-radiation-budget", 4),
            ("data-protection-privacy-statement", 24),
            ("eumetsat-cm-saf", 1),
            ("licence-to-use-copernicus-products", 12),
        ]
        session.commit()
        for licence_uid, revision in licence_attrs:
            licence_obj = session.scalars(
                sa.select(database.Licence).filter_by(
                    licence_uid=licence_uid, revision=revision
                )
            ).all()
            assert len(licence_obj) == 1


def test_remove_orphan_licences(session_obj: sa.orm.sessionmaker) -> None:
    resource_uids = ["datasetA", "datasetB", "datasetC"]
    licence_uids = [("licence_1", 1), ("licence_2", 1), ("licence_3", 1)]
    dataset_objs = dict()
    licence_objs = dict()
    with session_obj() as session:
        # add some datasets
        for resource_uid in resource_uids:
            dataset_obj = mock_dataset(resource_uid=resource_uid)
            session.add(dataset_obj)
            dataset_objs[resource_uid] = dataset_obj
        session.commit()
        # add some licences
        for licence_uid, revision in licence_uids:
            licence_obj = mock_licence(licence_uid=licence_uid, revision=revision)
            session.add(licence_obj)
            licence_objs[licence_uid] = licence_obj
        # add some relationships
        licence_objs["licence_1"].resources = [dataset_objs["datasetA"]]
        licence_objs["licence_2"].resources = [
            dataset_objs["datasetA"],
            dataset_objs["datasetB"],
        ]
        licence_objs["licence_3"].resources = [dataset_objs["datasetC"]]
        session.commit()

        # case 1: do not remove anything, all licences are to keep
        keep_licences = licence_uids
        licence_manager.remove_orphan_licences(session, keep_licences, resource_uids)
        session.commit()
        for licence_uid, revision in licence_uids:
            query_licences = session.scalars(
                sa.select(database.Licence).filter_by(
                    licence_uid=licence_uid, revision=revision
                )
            ).all()
            assert len(query_licences) == 1

        # case 2: do not remove anything, not to keep but they all have datasets
        keep_licences = []
        licence_manager.remove_orphan_licences(session, keep_licences, resource_uids)
        session.commit()
        for licence_uid, revision in licence_uids:
            query_licences = session.scalars(
                sa.select(database.Licence).filter_by(
                    licence_uid=licence_uid, revision=revision
                )
            ).all()
            assert len(query_licences) == 1

        # case 3: remove a licence, not to keep and unrelated to any dataset
        keep_licences = [
            ("licence_1", 1),
            ("licence_2", 1),
        ]
        licence_objs["licence_3"].resources = []
        licence_manager.remove_orphan_licences(session, keep_licences, resource_uids)
        session.commit()
        for licence_uid, revision in keep_licences:
            query_licences = session.scalars(
                sa.select(database.Licence).filter_by(
                    licence_uid=licence_uid, revision=revision
                )
            ).all()
            assert len(query_licences) == 1
            query_licences = session.scalars(
                sa.select(database.Licence).filter_by(
                    licence_uid="licence_3", revision=1
                )
            ).all()
            assert len(query_licences) == 0

        # case 4: remove a licence, not to keep and related to dataset not to keep
        keep_licences = []
        resource_uids = ["datasetB"]
        licence_manager.remove_orphan_licences(session, keep_licences, resource_uids)
        session.commit()
        query_licences = session.scalars(
            sa.select(database.Licence).filter_by(licence_uid="licence_2", revision=1)
        ).all()
        assert len(query_licences) == 1
        query_licences = session.scalars(
            sa.select(database.Licence).filter_by(licence_uid="licence_1", revision=1)
        ).all()
        assert len(query_licences) == 0
