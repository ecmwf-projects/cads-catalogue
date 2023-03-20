"""utility module to load and store data in the catalogue database."""

# Copyright 2022, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import json
import os
import pathlib
import shutil
import tempfile
import urllib.parse
from typing import Any, List

import sqlalchemy as sa
import structlog

from cads_catalogue import config, database, object_storage

logger = structlog.get_logger(__name__)


def manage_licence_block(
    req_licences: List[database.Licence],
    block: dict[str, Any],
    doc_storage_url: str,
):
    """
    Modify accordingly the licence block with ids and urls required.

    Parameters
    ----------
    req_licences: list of licence objects required by the dataset
    block: item of form.json data
    doc_storage_url: public url of the object storage
    """
    new_block = copy.deepcopy(block)
    if "details" not in new_block or not new_block["details"]:
        new_block["details"] = {"licences": []}

    licences_block = []
    for req_licence in req_licences:
        licence_block = {
            "id": req_licence.licence_uid,
            "revision": req_licence.revision,
            "label": req_licence.title,
            "contents_url": urllib.parse.urljoin(
                doc_storage_url, req_licence.md_filename
            ),
            "attachment_url": urllib.parse.urljoin(
                doc_storage_url, req_licence.download_filename
            ),
        }
        licences_block.append(licence_block)

    new_block["details"]["licences"] = licences_block
    return new_block


def transform_licences_blocks(
    session: sa.orm.session.Session,
    form_data: List[dict[str, Any]],
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
):
    """Transform layout.json data processing uploads of referenced licences.

    Parameters
    ----------
    session: opened SQLAlchemy session
    form_data: data of the layout.json to store
    resource: metadata of a loaded resource from files
    storage_settings: object with settings to access the object storage

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    new_data = copy.deepcopy(form_data)
    doc_storage_url = storage_settings.document_storage_url

    # get licence's metadata from db, but take list of licence uids from resource dictionary
    req_licences = []
    for licence_uid in resource["licence_uids"]:
        licence_obj = (
            session.query(database.Licence)
            .filter_by(licence_uid=licence_uid)
            .order_by(database.Licence.revision.desc())
            .first()
        )
        if not licence_obj:
            raise ValueError("licence_uid = %r not found" % licence_uid)
        req_licences.append(licence_obj)

    req_licences = (
        session.query(database.Resource)
        .filter_by(resource_uid=resource["resource_uid"])
        .licences
    )

    # search all licence blocks inside form items:
    for i, block in enumerate(copy.deepcopy(form_data)):
        if type == "LicenceWidget":
            new_data[i] = manage_licence_block(req_licences, block, doc_storage_url)

    return new_data


def store_form_by_data(
    form_data: List[dict[str, Any]],
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
) -> str:
    """
    Store a layout.json in the object storage providing its json data.

    Parameters
    ----------
    form_data: data of the layout.json to store
    resource: resource dictionary (as returned by `load_resource_from_folder`)
    storage_settings: object with settings to access the object storage

    Returns
    -------
    str: URL of the layout.json uploaded to the object storage
    """
    # upload of modified form.json
    tempdir_path = tempfile.mkdtemp()
    subpath = os.path.join("resources", resource["resource_uid"])
    form_temp_path = os.path.join(tempdir_path, "form.json")
    with open(form_temp_path, "w") as fp:
        json.dump(form_data, fp, indent=2)
    try:
        form_url = object_storage.store_file(
            form_temp_path,
            storage_settings.object_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            subpath=subpath,
            force=True,
            **storage_settings.storage_kws,
        )[0]
    finally:
        shutil.rmtree(tempdir_path)
    return form_url


def transform_form(
    session: sa.orm.session.Session,
    resource_folder_path: str | pathlib.Path,
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
):
    """
    Modify form.json information inside resource metadata.

    Parameters
    ----------
    session: opened SQLAlchemy session
    resource_folder_path: folder path where to find layout.json
    resource: metadata of a loaded resource from files
    storage_settings: object with settings to access the object storage

    Returns
    -------
    modified version of input resource metadata
    """
    metadata: dict[str, Any] = dict()
    form_file_path = os.path.join(resource_folder_path, "form.json")
    if not os.path.isfile(form_file_path):
        return metadata
    with open(form_file_path) as fp:
        form_data = json.load(fp)
    form_data = transform_licences_blocks(
        session, form_data, resource, storage_settings
    )
    resource["form_data"] = form_data
    resource["form"] = store_form_by_data(form_data, resource, storage_settings)
    return resource
