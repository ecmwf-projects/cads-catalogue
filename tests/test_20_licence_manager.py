import operator
import os.path

import pytest_mock
from sqlalchemy.orm import sessionmaker

from cads_catalogue import config, database, licence_manager, utils

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def test_licence_sync(
    session_obj: sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    licence_uid = "CCI-data-policy-for-satellite-surface-radiation-budget"
    licence_md = {
        "licence_id": 1,
        "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
        "revision": 4,
        "title": "CCI product licence",
        "download_filename": "an url",
        "scope": "dataset",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    # start without any licence in the db
    with session_obj() as session:
        licence_manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.query(database.Licence).all()
        assert len(db_licences) == 1
        assert utils.object_as_dict(db_licences[0]) == licence_md

    assert patch.call_count == 1
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
        "force": True,
        "access_key": "admin1",
        "secret_key": "secret1",
        "secure": False,
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
    }
    licences = [updated_licence]
    with session_obj() as session:
        licence_manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.query(database.Licence).all()
        assert len(db_licences) == 1
        assert utils.object_as_dict(db_licences[0]) == licence_md2

    # reset globals for tests following
    config.dbsettings = None
    config.storagesettings = None


def test_load_licences_from_folder() -> None:
    # test data taken from repository "https://git.ecmwf.int/projects/CDS/repos/cds-licences"
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    expected_licences = [
        {
            "download_filename": os.path.join(
                licences_folder_path,
                "CCI-data-policy-for-satellite-surface-radiation-budget.pdf",
            ),
            "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
            "revision": 4,
            "title": "CCI product licence",
            "scope": "dataset",
        },
        {
            "download_filename": os.path.join(
                licences_folder_path, "eumetsat-cm-saf.pdf"
            ),
            "licence_uid": "eumetsat-cm-saf",
            "revision": 1,
            "title": "EUMETSAT CM SAF products licence",
            "scope": "dataset",
        },
        {
            "download_filename": os.path.join(
                licences_folder_path, "licence-to-use-copernicus-products.pdf"
            ),
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
            "scope": "dataset",
        },
    ]
    licences = sorted(
        licence_manager.load_licences_from_folder(licences_folder_path),
        key=operator.itemgetter("licence_uid"),
    )

    assert licences == expected_licences
