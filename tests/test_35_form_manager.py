import json
import operator
import os.path
import urllib.parse
from typing import Any

import pytest_mock
from sqlalchemy.orm import sessionmaker

from cads_catalogue import (
    config,
    database,
    form_manager,
    licence_manager,
    object_storage,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def create_form_for_test(path, items=[]):
    """Use for testing."""
    with open(path, "w") as fp:
        json.dump(items, fp)
    return items


def test_build_licence_block(session_obj: sessionmaker):
    doc_storage_url = "http://my/url/"

    # add some licences to work on
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    with session_obj() as session:
        for licence in licences:
            session.add(database.Licence(**licence))
        session.commit()
        req_licences = session.query(database.Licence).all()
    req_licences = sorted(req_licences, key=operator.attrgetter("licence_uid"))

    new_block = form_manager.build_licence_block(req_licences, doc_storage_url)

    assert new_block == {
        "details": {
            "licences": [
                {
                    "attachment_url": urllib.parse.urljoin(
                        doc_storage_url, req_licences[0].download_filename
                    ),
                    "contents_url": urllib.parse.urljoin(
                        doc_storage_url, req_licences[0].md_filename
                    ),
                    "id": "CCI-data-policy-for-satellite-surface-radiation-budget",
                    "label": "CCI product licence",
                    "revision": 4,
                },
                {
                    "attachment_url": urllib.parse.urljoin(
                        doc_storage_url, req_licences[1].download_filename
                    ),
                    "contents_url": urllib.parse.urljoin(
                        doc_storage_url, req_licences[1].md_filename
                    ),
                    "id": "eumetsat-cm-saf",
                    "label": "EUMETSAT CM SAF products licence",
                    "revision": 1,
                },
                {
                    "attachment_url": urllib.parse.urljoin(
                        doc_storage_url, req_licences[2].download_filename
                    ),
                    "contents_url": urllib.parse.urljoin(
                        doc_storage_url, req_licences[2].md_filename
                    ),
                    "id": "licence-to-use-copernicus-products",
                    "label": "Licence to use Copernicus Products",
                    "revision": 12,
                },
            ]
        },
        "help": None,
        "label": "Terms of use",
        "name": "licences",
        "type": "LicenceWidget",
    }


def test_transform_licences_blocks(session_obj: sessionmaker):
    oss = config.ObjectStorageSettings(
        object_storage_url="http://myobject-storage:myport/",
        storage_admin="storage_user",
        storage_password="storage_password",
        catalogue_bucket="abucket",
        document_storage_url="http://public-storage/",
    )

    # add some licences to work on
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    with session_obj() as session:
        for licence in licences:
            session.add(database.Licence(**licence))
        session.commit()
        req_licences = session.query(database.Licence).all()
    req_licences = sorted(req_licences, key=operator.attrgetter("licence_uid"))
    resource = {
        "resource_uid": "a-dataset",
        "licence_uids": [req_licences[0].licence_uid],
    }
    form_item1: dict[str, Any] = {
        "name": "origin",
        "label": "Origin",
        "help": None,
        "required": True,
        "css": "todo",
        "type": "StringListWidget",
        "details": {},
        "id": 0,
    }
    form_data = [form_item1]
    new_form_data = form_manager.transform_licences_blocks(
        session, form_data, resource, oss
    )

    assert new_form_data != form_data
    assert new_form_data == [
        form_item1,
        {
            "type": "LicenceWidget",
            "name": "licences",
            "label": "Terms of use",
            "help": None,
            "details": {
                "licences": [
                    {
                        "attachment_url": urllib.parse.urljoin(
                            "http://public-storage/", req_licences[0].download_filename
                        ),
                        "contents_url": urllib.parse.urljoin(
                            "http://public-storage/", req_licences[0].md_filename
                        ),
                        "id": "CCI-data-policy-for-satellite-surface-radiation-budget",
                        "label": "CCI product licence",
                        "revision": 4,
                    },
                ]
            },
        },
    ]


def test_transform_form(
    tmpdir, session_obj: sessionmaker, mocker: pytest_mock.MockerFixture
):
    oss = config.ObjectStorageSettings(
        object_storage_url="http://myobject-storage:myport/",
        storage_admin="storage_user",
        storage_password="storage_password",
        catalogue_bucket="abucket",
        document_storage_url="http://public-storage/",
    )
    mocker.patch.object(
        object_storage, "store_file", return_value="an url for form.json"
    )
    # add some licences to work on
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    with session_obj() as session:
        for licence in licences:
            session.add(database.Licence(**licence))
        session.commit()
        req_licences = session.query(database.Licence).all()
    req_licences = sorted(req_licences, key=operator.attrgetter("licence_uid"))

    resource = {
        "resource_uid": "a-dataset",
        "licence_uids": [req_licences[0].licence_uid, req_licences[2].licence_uid],
    }

    form_path = os.path.join(str(tmpdir), "form.json")
    form_item1: dict[str, Any] = {
        "name": "origin",
        "label": "Origin",
        "help": None,
        "required": True,
        "css": "todo",
        "type": "StringListWidget",
        "details": {},
        "id": 0,
    }
    items = [form_item1, form_item1, form_item1]
    create_form_for_test(form_path, items)

    new_resource = form_manager.transform_form(session, str(tmpdir), resource, oss)

    for key in resource:
        assert key in new_resource
        assert new_resource[key] == resource[key]
    assert new_resource["form"] == "an url for form.json"
    assert new_resource["form_data"] == [
        form_item1,
        form_item1,
        form_item1,
        {
            "type": "LicenceWidget",
            "name": "licences",
            "label": "Terms of use",
            "help": None,
            "details": {
                "licences": [
                    {
                        "attachment_url": urllib.parse.urljoin(
                            "http://public-storage/", req_licences[0].download_filename
                        ),
                        "contents_url": urllib.parse.urljoin(
                            "http://public-storage/", req_licences[0].md_filename
                        ),
                        "id": "CCI-data-policy-for-satellite-surface-radiation-budget",
                        "label": "CCI product licence",
                        "revision": 4,
                    },
                    {
                        "attachment_url": urllib.parse.urljoin(
                            "http://public-storage/", req_licences[2].download_filename
                        ),
                        "contents_url": urllib.parse.urljoin(
                            "http://public-storage/", req_licences[2].md_filename
                        ),
                        "id": "licence-to-use-copernicus-products",
                        "label": "Licence to use Copernicus Products",
                        "revision": 12,
                    },
                ]
            },
        },
    ]
