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
from typing import Any, List, Sequence

import sqlalchemy as sa
import structlog

from cads_catalogue import config, database, object_storage, utils

logger = structlog.get_logger(__name__)


def manage_image_section(
    folder_path: str | pathlib.Path,
    section: dict[str, Any],
    images_stored: dict[str, str],
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings | Any,
    disable_upload: bool = False,
):
    """
    Look for thumb-markdown blocks and modify accordingly with upload to object storage.

    Parameters
    ----------
    folder_path: folder path where to find layout.json
    section: section of layout.json data
    images_stored: dictionary of image urls already stored
    resource: metadata of loaded resource
    storage_settings: object with settings to access the object storage
    disable_upload: disable upload (for testing, default False)
    """
    new_section = copy.deepcopy(section)
    blocks = new_section.get("blocks", [])
    for i, block in enumerate(copy.deepcopy(blocks)):
        image_dict = block.get("image", {})
        image_rel_path = image_dict.get("url")
        if block.get("type") == "thumb-markdown" and image_rel_path:
            if utils.is_url(image_rel_path):
                # nothing to do, the url is already uploaded somewhere
                continue
            image_abs_path = os.path.join(folder_path, block["image"]["url"])
            if os.path.isfile(image_abs_path):
                if image_abs_path not in images_stored and not disable_upload:
                    # process upload to object storage
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
                        **storage_settings.storage_kws,
                    )
                    # update cache of the upload urls
                    images_stored[image_abs_path] = urllib.parse.urljoin(
                        storage_settings.document_storage_url, image_rel_url
                    )
                blocks[i]["image"]["url"] = images_stored.get(image_abs_path, "")
            else:
                raise ValueError(f"image {image_rel_path} not found")
        elif block.get("type") in ("section", "accordion"):
            blocks[i] = manage_image_section(
                folder_path,
                block,
                images_stored,
                resource,
                storage_settings,
                disable_upload=disable_upload,
            )
    return new_section


def transform_image_blocks(
    layout_data: dict[str, Any],
    folder_path: str | pathlib.Path,
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings | Any,
    disable_upload: bool = False,
) -> dict[str, Any]:
    """Transform layout.json data processing uploads of referenced images.

    Parameters
    ----------
    layout_data: layout.json input content
    folder_path: folder path where to find layout.json
    resource: metadata of loaded resource
    storage_settings: object with settings to access the object storage
    disable_upload: disable upload (for testing/validations, default False)

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    images_stored: dict[str, str] = dict()
    new_data = copy.deepcopy(layout_data)
    # search all the images inside body/main/sections:
    body = new_data.get("body", {})
    body_main = body.get("main", {})
    sections = body_main.get("sections", [])
    for i, section in enumerate(copy.deepcopy(sections)):
        sections[i] = manage_image_section(
            folder_path,
            section,
            images_stored,
            resource,
            storage_settings,
            disable_upload=disable_upload,
        )
    # search all the images inside body/aside:
    aside_section = new_data.get("body", {}).get("aside", {})
    if aside_section:
        new_data["body"]["aside"] = manage_image_section(
            folder_path,
            aside_section,
            images_stored,
            resource,
            storage_settings,
            disable_upload=disable_upload,
        )
    return new_data


def build_required_licence_blocks(
    licence: database.Licence, doc_storage_url: str
) -> List[dict[str, str]]:
    """
    Build a list of blocks related to required licences to be inserted inside the layout data.

    Parameters
    ----------
    licence: related licence object
    doc_storage_url: public base url of the document storage

    Returns
    -------
    list of 3 new licence blocks for the layout data
    """
    new_blocks = [
        {
            "type": "button",
            "id": f"{licence.licence_uid}-licences",
            "title": f"{licence.title}",
            "action": "modal",
            "contents-url": urllib.parse.urljoin(doc_storage_url, licence.md_filename),
        },
        {
            "type": "button",
            "id": f"{licence.licence_uid}-licences-download",
            "parent": f"{licence.licence_uid}-licences",
            "title": "Download PDF",
            "action": "download",
            "contents-url": urllib.parse.urljoin(
                doc_storage_url, licence.download_filename
            ),
        },
        {
            "type": "button",
            "id": f"{licence.licence_uid}-licences-clipboard",
            "parent": f"{licence.licence_uid}-licences",
            "title": "Copy to clipboard",
            "action": "copy-clipboard",
        },
    ]
    return new_blocks


def manage_required_licence_section(
    all_licences: Sequence[database.Licence],
    section: dict[str, Any],
    doc_storage_url: str,
):
    """
    Look for required licence blocks and modify accordingly with urls of object storage files.

    Parameters
    ----------
    all_licences: list of licence objects in the database
    section: section of layout.json data
    doc_storage_url: public url of the object storage
    """
    new_section = copy.deepcopy(section)
    blocks = new_section.get("blocks", [])
    replacements = 0
    for i, block in enumerate(copy.deepcopy(blocks)):
        if block.get("type") == "licence":
            licence_uid = block["licence-id"]
            try:
                licence = [
                    r for r in all_licences if r.licence_uid == block["licence-id"]
                ][0]
            except IndexError:
                raise ValueError(f"not found licence {licence_uid}")
            new_blocks = build_required_licence_blocks(licence, doc_storage_url)
            del blocks[i + 2 * replacements]
            blocks.insert(i + 2 * replacements, new_blocks[0])
            blocks.insert(i + 1 + 2 * replacements, new_blocks[1])
            blocks.insert(i + 2 + 2 * replacements, new_blocks[2])
            replacements += 1
        elif block.get("type") in ("section", "accordion"):
            blocks[i + 2 * replacements] = manage_required_licence_section(
                all_licences, block, doc_storage_url
            )
    return new_section


def transform_licence_required_blocks(
    session: sa.orm.session.Session,
    layout_data: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
):
    """Transform layout.json replacing blocks related to required licences.

    Parameters
    ----------
    session: opened SQLAlchemy session
    layout_data: data of the layout.json to store
    storage_settings: object with settings to access the object storage

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    new_data = copy.deepcopy(layout_data)
    doc_storage_url = storage_settings.document_storage_url
    all_licences = session.scalars(sa.select(database.Licence)).all()

    # search all licence blocks inside body/main/sections:
    body = new_data.get("body", {})
    body_main = body.get("main", {})
    sections = body_main.get("sections", [])
    for i, section in enumerate(copy.deepcopy(sections)):
        sections[i] = manage_required_licence_section(
            all_licences, section, doc_storage_url
        )
    # search all the images inside body/aside:
    aside_section = body.get("aside", {})
    if aside_section:
        new_data["body"]["aside"] = manage_required_licence_section(
            all_licences,
            aside_section,
            doc_storage_url,
        )
    return new_data


def build_licence_acceptance_block(
    licence_objs: List[database.Licence], doc_storage_url: str
) -> dict[str, Any]:
    """
    Build a new licence acceptance block to be inserted inside the layout data.

    Parameters
    ----------
    licence_objs: list of related licence objects
    doc_storage_url: public base url of the document storage

    Returns
    -------
    new licence block for the layout data
    """
    licence_blocks = []
    for licence_obj in licence_objs:
        licence_block = {
            "id": f"{licence_obj.licence_uid}",
            "revision": licence_obj.revision,
            "label": f"{licence_obj.title}",
            "contents_url": urllib.parse.urljoin(
                doc_storage_url, licence_obj.md_filename
            ),
            "attachment_url": urllib.parse.urljoin(
                doc_storage_url, licence_obj.download_filename
            ),
        }
        licence_blocks.append(licence_block)
    new_block = {
        "type": "licences_acceptance",
        "details": {"licences": licence_blocks},
    }
    return new_block


def manage_licence_acceptance_section(
    all_licences: Sequence[database.Licence],
    section: dict[str, Any],
    doc_storage_url: str,
):
    """
    Look for licence acceptance blocks and modify accordingly with urls of object storage files.

    Parameters
    ----------
    all_licences: list of licence objects in the database
    section: section of layout.json data
    doc_storage_url: public url of the object storage
    """
    new_section = copy.deepcopy(section)
    blocks = new_section.get("blocks", [])
    for i, block in enumerate(copy.deepcopy(blocks)):
        if block.get("type") == "licences_acceptance" and "details" in block:
            licence_objs = []
            for licence_block in block["details"]["licences"]:
                licence_uid = licence_block["licence-id"]
                try:
                    licence_obj = [
                        r
                        for r in all_licences
                        if r.licence_uid == licence_block["licence-id"]
                    ][0]
                except IndexError:
                    raise ValueError(f"not found licence {licence_uid}")
                licence_objs.append(licence_obj)
            new_block = build_licence_acceptance_block(licence_objs, doc_storage_url)
            for attr in ("id", "title"):
                attr_value = block.get(attr)
                if attr_value:
                    new_block[attr] = attr_value
            del blocks[i]
            blocks.insert(i, new_block)
        elif block.get("type") in ("section", "accordion"):
            blocks[i] = manage_licence_acceptance_section(
                all_licences, block, doc_storage_url
            )
    return new_section


def transform_licence_acceptance_blocks(
    session: sa.orm.session.Session,
    layout_data: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
):
    """Transform layout.json replacing blocks related to licence acceptance.

    Parameters
    ----------
    session: opened SQLAlchemy session
    layout_data: data of the layout.json to store
    storage_settings: object with settings to access the object storage

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    new_data = copy.deepcopy(layout_data)
    doc_storage_url = storage_settings.document_storage_url
    all_licences = session.scalars(sa.select(database.Licence)).all()

    # search all licence blocks inside body/main/sections:
    body = new_data.get("body", {})
    body_main = body.get("main", {})
    sections = body_main.get("sections", [])
    for i, section in enumerate(copy.deepcopy(sections)):
        sections[i] = manage_licence_acceptance_section(
            all_licences, section, doc_storage_url
        )
    # search all the images inside body/aside:
    aside_section = body.get("aside", {})
    if aside_section:
        new_data["body"]["aside"] = manage_licence_acceptance_section(
            all_licences,
            aside_section,
            doc_storage_url,
        )
    return new_data


def transform_cim_blocks(
    layout_data: dict[str, Any], cim_layout_path: str, qa_flag: bool = True
):
    """Transform layout.json data according to CIM Quality Assessment layout.

    Parameters
    ----------
    layout_data: data of the layout.json to transform
    cim_layout_path: path to the file containing CIM Quality Assessment
    qa_flag: if False, remove QA placeholders from layout_data regardless the cim layout

    Returns
    -------
    dict: dictionary of layout_data modified
    """
    remove_tab = True
    remove_aside = True
    cim_layout_data = dict()
    if os.path.exists(cim_layout_path):
        with open(cim_layout_path) as fp:
            cim_layout_data = json.load(fp)
    qa_tab = cim_layout_data.get("quality_assurance_tab", {})
    qa_tab_blocks = qa_tab.get("blocks")
    if qa_tab_blocks is not None and qa_flag:
        remove_tab = False
    qa_aside = cim_layout_data.get("quality_assurance_aside", {})
    qa_aside_blocks = qa_aside.get("blocks")
    if qa_aside_blocks is not None and qa_flag:
        remove_aside = False
    new_data = copy.deepcopy(layout_data)
    body = new_data.get("body", {})
    body_main = body.get("main", {})
    sections = body_main.get("sections", [])
    aside = body.get("aside", {})
    aside_blocks = aside.get("blocks", [])

    for i, section in enumerate(copy.deepcopy(sections)):
        if section.get("id") == "quality_assurance_tab":
            if remove_tab:
                del sections[i]
            else:
                sections[i] = qa_tab
            break

    for i, aside_block in enumerate(copy.deepcopy(aside_blocks)):
        if aside_block.get("id") == "quality_assurance_aside":
            if remove_aside:
                del aside_blocks[i]
            else:
                aside_blocks[i] = qa_aside
            break
    return new_data


def has_section_id(layout_data: dict[str, Any], section_id: str):
    """
    Return True if layout has section id `section_id`.

    Parameters
    ----------
    layout_data: data of the layout.json to check
    section_id: id of the section inside body-> main -> sections

    Returns
    -------
    True if id of the section is found, False otherwise.
    """
    body = layout_data.get("body", {})
    body_main = body.get("main", {})
    sections = body_main.get("sections", [])
    for section in sections:
        if section.get("id") == section_id:
            return True
    return False


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
        json.dump(layout_data, fp, indent=2)
    try:
        layout_url = object_storage.store_file(
            layout_temp_path,
            storage_settings.object_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            subpath=subpath,
            **storage_settings.storage_kws,
        )
    finally:
        shutil.rmtree(tempdir_path)
    return layout_url


def transform_layout(
    session: sa.orm.session.Session,
    resource_folder_path: str | pathlib.Path,
    cim_folder_path: str | pathlib.Path,
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
    cim_folder_path: the folder path containing CIM generated Quality Assessment layouts
    storage_settings: object with settings to access the object storage

    Returns
    -------
    modified version of input resource metadata
    """
    layout_file_path = os.path.join(resource_folder_path, "layout.json")
    resource["layout"] = None
    if not os.path.isfile(layout_file_path):
        return resource
    with open(layout_file_path) as fp:
        layout_data = json.load(fp)
        logger.debug(f"input layout_data: {layout_data}")
    cim_layout_path = os.path.join(
        cim_folder_path, resource["resource_uid"], "quality_assurance.layout.json"
    )
    layout_data = transform_cim_blocks(
        layout_data, cim_layout_path, resource["qa_flag"]
    )
    layout_data = transform_image_blocks(
        layout_data, resource_folder_path, resource, storage_settings
    )
    layout_data = transform_licence_required_blocks(
        session, layout_data, storage_settings
    )
    layout_data = transform_licence_acceptance_blocks(
        session, layout_data, storage_settings
    )
    logger.debug(f"output layout_data: {layout_data}")
    if resource["qa_flag"]:
        resource["qa_flag"] = has_section_id(layout_data, "quality_assurance_tab")
    resource["layout"] = store_layout_by_data(layout_data, resource, storage_settings)
    logger.debug(f"layout url: {resource['layout']}")
    return resource
