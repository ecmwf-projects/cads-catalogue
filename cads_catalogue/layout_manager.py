"""processing module of layout.json for the catalogue manager."""

# Copyright 2023, European Union.
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
from typing import Any

import structlog
from sqlalchemy.orm.session import Session

from cads_catalogue import config, object_storage

logger = structlog.get_logger(__name__)


def transform_image_blocks(
    layout_data: dict[str, Any],
    folder_path:  str | pathlib.Path,
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
) -> dict[str, Any]:
    """Transform layout.json data processing uploads of referenced images.

    Parameters
    ----------
    layout_data: layout.json input content
    folder_path: folder path where to find layout.json
    resource: metadata of loaded resource
    storage_settings: object with settings to access the object storage

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    images_stored = dict()
    new_data = copy.deepcopy(layout_data)
    layout_file_path = os.path.join(folder_path, "layout.json")
    # search all the images inside body/main/sections:
    sections = layout_data.get("body", {}).get("main", {}).get("sections", [])
    for i, section in enumerate(sections):
        blocks = section.get("blocks", [])
        for j, block in enumerate(blocks):
            image_rel_path = block.get("image", {}).get("url")
            if block.get("type") == "thumb-markdown" and image_rel_path:
                image_abs_path = os.path.join(folder_path, block["image"]["url"])
                if os.path.isfile(image_abs_path):
                    if image_abs_path not in images_stored:
                        subpath = os.path.dirname(
                            os.path.join(
                                "resources", resource["resource_uid"], image_rel_path
                            )
                        )
                        image_rel_url = object_storage.store_file(
                            image_abs_path,
                            storage_settings.object_storage_url,
                            bucket_name=storage_settings.catalogue_bucket,
                            subpath=subpath,
                            force=True,
                            **storage_settings.storage_kws,
                        )[0]
                        images_stored[image_abs_path] = urllib.parse.urljoin(
                            storage_settings.document_storage_url, image_rel_url
                        )
                    new_data["body"]["main"]["sections"][i]["blocks"][j]["image"][
                        "url"
                    ] = images_stored[image_abs_path]
                else:
                    raise ValueError(
                        "image %r referenced on %r not found"
                        % (image_rel_path, layout_file_path)
                    )
    # search all the images inside body/aside:
    aside_blocks = layout_data.get("body", {}).get("aside", {}).get("blocks", [])
    for i, block in enumerate(aside_blocks):
        image_rel_path = block.get("image", {}).get("url")
        if block.get("type") == "thumb-markdown" and image_rel_path:
            image_abs_path = os.path.join(folder_path, block["image"]["url"])
            if os.path.isfile(image_abs_path):
                if image_abs_path not in images_stored:
                    subpath = os.path.dirname(
                        os.path.join(
                            "resources", resource["resource_uid"], image_rel_path
                        )
                    )
                    image_rel_url = object_storage.store_file(
                        image_abs_path,
                        storage_settings.object_storage_url,
                        bucket_name=storage_settings.catalogue_bucket,
                        subpath=subpath,
                        force=True,
                        **storage_settings.storage_kws,
                    )[0]
                    images_stored[image_abs_path] = urllib.parse.urljoin(
                        storage_settings.document_storage_url, image_rel_url
                    )
                new_data["body"]["aside"]["blocks"][i]["image"]["url"] = images_stored[
                    image_abs_path
                ]
            else:
                raise ValueError(
                    "image %r referenced on %r not found"
                    % (image_rel_path, layout_file_path)
                )
    return new_data


def transform_licences_blocks(
    session: Session,
    layout_data: dict[str, Any],
    resource_folder_path: str | pathlib.Path,
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
):
    """Transform layout.json data processing uploads of referenced licences.

    Parameters
    ----------
    session: opened SQLAlchemy session
    layout_data: data of the layout.json to store
    resource_folder_path
    resource: resource dictionary (as returned by `load_resource_from_folder`)
    storage_settings: object with settings to access the object storage

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    # TODO
    return layout_data


def store_layout_by_data(
    layout_data: dict[str, Any],
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
) -> str:
    """
    Store a layout.json in the object storage providing its json data.

    Parameters
    ----------
    layout_data: data of the layout.json to store
    resource: resource dictionary (as returned by `load_resource_from_folder`)
    storage_settings: object with settings to access the object storage

    Returns
    -------
    str: URL of the layout.json uploaded to the object storage
    """
    # upload of modified layout.json
    tempdir_path = tempfile.mkdtemp()
    subpath = os.path.join("resources", resource["resource_uid"])
    layout_temp_path = os.path.join(tempdir_path, "layout.json")
    with open(layout_temp_path, "w") as fp:
        json.dump(layout_data, fp)
    try:
        layout_url = object_storage.store_file(
            layout_temp_path,
            storage_settings.object_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            subpath=subpath,
            force=True,
            **storage_settings.storage_kws,
        )[0]
    finally:
        shutil.rmtree(tempdir_path)
    return layout_url


def transform_layout(
    session: Session,
    resource_folder_path: str | pathlib.Path,
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
):
    """
    Modify layout.json information inside resource metadata, with related uploads to the object storage.

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
    layout_file_path = os.path.join(resource_folder_path, "layout.json")
    if not os.path.isfile(layout_file_path):
        return metadata
    with open(layout_file_path) as fp:
        layout_data = json.load(fp)
    layout_data = transform_image_blocks(
        layout_data, resource_folder_path, resource, storage_settings
    )
    layout_data = transform_licences_blocks(
        session, layout_data, resource_folder_path, resource, storage_settings
    )
    resource["layout"] = store_layout_by_data(layout_data, resource, storage_settings)
    # create a temporary file with new layout.json, upload to the object storage and modify resource['layout']
    return resource
