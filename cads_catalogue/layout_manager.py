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

import json
import os
import pathlib
import shutil
import tempfile
import urllib.parse
from typing import Any, List, Tuple

import structlog

from cads_catalogue import object_storage

logger = structlog.get_logger(__name__)


def load_layout_images_info(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load a resource's layout.json metadata and collect information about referenced images.

    Return a dictionary with a key 'layout_images_info' loaded with a list of tuples containing
    information about the image files found and their positions inside the json.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata: dict[str, Any] = dict()
    layout_file_path = os.path.join(folder_path, "layout.json")
    if not os.path.isfile(layout_file_path):
        return metadata
    with open(layout_file_path) as fp:
        layout_data = json.load(fp)
    images_found: List[Tuple[str, str, int] | Tuple[str, str, int, int]] = []
    # search all the images inside body/main/sections:
    sections = layout_data.get("body", {}).get("main", {}).get("sections", [])
    for i, section in enumerate(sections):
        blocks = section.get("blocks", [])
        for j, block in enumerate(blocks):
            image_rel_path = block.get("image", {}).get("url")
            if block.get("type") == "thumb-markdown" and image_rel_path:
                image_abs_path = os.path.join(folder_path, block["image"]["url"])
                if os.path.isfile(image_abs_path):
                    image_info = (
                        image_abs_path,
                        "sections",
                        i,
                        j,
                    )
                    images_found.append(image_info)
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
                image_info2 = (image_abs_path, "aside", i)
                images_found.append(image_info2)
    metadata["layout_images_info"] = images_found
    return metadata


def manage_upload_layout_images(
    dataset: dict[str, Any],
    object_storage_url: str,
    doc_storage_url: str,
    bucket_name: str = "cads-catalogue",
    **storage_kws: Any,
) -> dict[str, Any]:
    """Upload images referenced in the layout.json and return a modified json data with images' URLs.

    Parameters
    ----------
    dataset: resource dictionary (as returned by `load_resource_from_folder`)
    object_storage_url: endpoint URL of the object storage (for upload)
    doc_storage_url: public endpoint URL of the object storage (for download)
    bucket_name: bucket name of the object storage to use
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    data of the layout.json modified
    """
    layout_file_path = dataset["layout"]
    with open(layout_file_path) as fp:
        layout_data = json.load(fp)
    # uploads images to object storage and modification of layout's json
    images_stored = dict()
    for image_info in dataset["layout_images_info"]:
        if image_info[1] == "sections":
            image_abs_path, _, i, j = image_info
            image_rel_path = layout_data["body"]["main"]["sections"][i]["blocks"][j][
                "image"
            ]["url"]
            subpath = os.path.dirname(
                os.path.join("resources", dataset["resource_uid"], image_rel_path)
            )
            if image_abs_path not in images_stored:
                image_rel_url = object_storage.store_file(
                    image_abs_path,
                    object_storage_url,
                    bucket_name=bucket_name,
                    subpath=subpath,
                    force=True,
                    **storage_kws,
                )[0]
                images_stored[image_abs_path] = urllib.parse.urljoin(
                    doc_storage_url, image_rel_url
                )
            layout_data["body"]["main"]["sections"][i]["blocks"][j]["image"][
                "url"
            ] = images_stored[image_abs_path]
        else:  # image_info[1] == 'aside'
            image_abs_path, _, i = image_info
            image_rel_path = layout_data["body"]["aside"]["blocks"][i]["image"]["url"]
            subpath = os.path.dirname(
                os.path.join("resources", dataset["resource_uid"], image_rel_path)
            )
            if image_abs_path not in images_stored:
                image_rel_url = object_storage.store_file(
                    image_abs_path,
                    object_storage_url,
                    bucket_name=bucket_name,
                    subpath=subpath,
                    force=True,
                    **storage_kws,
                )[0]
                images_stored[image_abs_path] = urllib.parse.urljoin(
                    doc_storage_url, image_rel_url
                )
            layout_data["body"]["aside"]["blocks"][i]["image"]["url"] = images_stored[
                image_abs_path
            ]
    return layout_data


def store_layout_by_data(
    dataset: dict[str, Any],
    layout_data: dict[str, Any],
    object_storage_url: str,
    bucket_name: str = "cads-catalogue",
    **storage_kws: Any,
) -> str:
    """
    Store a layout.json in the object storage providing its json data.

    Parameters
    ----------
    dataset: resource dictionary (as returned by `load_resource_from_folder`)
    layout_data: data of the layout.json to store
    object_storage_url: endpoint URL of the object storage (for upload)
    bucket_name: bucket name of the object storage to use
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    str: URL of the layout.json uploaded to the object storage
    """
    # upload of modified layout.json
    tempdir_path = tempfile.mkdtemp()
    subpath = os.path.join("resources", dataset["resource_uid"])
    layout_temp_path = os.path.join(tempdir_path, "layout.json")
    with open(layout_temp_path, "w") as new_layout_fp:
        json.dump(layout_data, new_layout_fp)
    try:
        layout_url = object_storage.store_file(
            layout_temp_path,
            object_storage_url,
            bucket_name=bucket_name,
            subpath=subpath,
            force=True,
            **storage_kws,
        )[0]
    finally:
        shutil.rmtree(tempdir_path)
    return layout_url
