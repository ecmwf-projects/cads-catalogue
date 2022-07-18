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

import glob
import itertools
import json
import os
import pathlib
import shutil
from typing import Any

import yaml
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from yaml.loader import SafeLoader

from cads_catalogue import database


def object_as_dict(obj: Any) -> dict[str, Any]:
    """Convert a sqlalchemy object in a python dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def save_in_document_storage(
    file_path: str | pathlib.Path,
    doc_storage_path: str | pathlib.Path | None = None,
    subpath: str = "",
) -> str | None:
    """Store a file in the document storage.

    Store a file at `file_path` in the document storage, in the path
    <doc_storage_path>/<subpath>/<file_name>.
    Return the relative path <subpath>/<file_name> of the file stored. or None if not stored.

    Parameters
    ----------
    file_path: absolute path to the file to store
    doc_storage_path: base folder path where to store the file
    subpath: optional folder path inside the document storage (created if not existing)

    Returns
    -------
    str | Path: the relative path <subpath>/<file_name> of the file stored.
    """
    if not file_path or not os.path.isabs(file_path) or not os.path.exists(file_path):
        print("warning: not found referenced file %r" % file_path)
        return None
    doc_storage_path = doc_storage_path or os.environ.get("DOCUMENT_STORAGE")
    if not doc_storage_path:
        print("warning: DOCUMENT STORAGE not set")
        return None
    file_name = os.path.basename(file_path)
    storage_rel_path = os.path.join(subpath, file_name)
    storage_abs_path = os.path.join(doc_storage_path, subpath)
    os.makedirs(storage_abs_path, exist_ok=True)
    shutil.copy(file_path, storage_abs_path)
    return storage_rel_path


def load_licences_from_folder(folder_path: str | pathlib.Path) -> list[dict[str, Any]]:
    """Load licences metadata from json files contained in a folder.

    Parameters
    ----------
    folder_path: the folder path where to look for json files

    Returns
    -------
    list: list of dictionaries of metadata collected
    """
    licences = []
    json_filepaths = glob.glob(os.path.join(folder_path, "*.json"))
    for json_filepath in json_filepaths:
        if "deprecated" in os.path.basename(json_filepath).lower():
            continue
        with open(json_filepath) as fp:
            json_data = json.load(fp)
            try:
                licence = {
                    "licence_uid": json_data["id"],
                    "revision": json_data["revision"],
                    "title": json_data["title"],
                    "download_filename": os.path.abspath(
                        os.path.join(folder_path, json_data["downloadableFilename"])
                    ),
                }
            except KeyError:
                continue
            licences.append(licence)
    return licences


def load_resource_from_folder(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load metadata of a resource from a folder.

    Parameters
    ----------
    folder_path: folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    file_names = os.listdir(folder_path)
    metadata: dict[str, Any] = dict()
    metadata["resource_uid"] = os.path.basename(folder_path)
    if "abstract.md" in file_names:
        with open(os.path.join(folder_path, "abstract.md")) as fp:
            metadata["abstract"] = fp.read()
    if "abstract.yaml" in file_names:
        with open(os.path.join(folder_path, "abstract.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["description"] = data.get("description")
            metadata["keywords"] = data.get("keywords")
            metadata["variables"] = data.get("variables")
            # NOTE: related_resources_keywords is for self-relationship, not a db field
            metadata["related_resources_keywords"] = data.get(
                "related_resources_keywords", []
            )
    if "dataset.yaml" in file_names:
        with open(os.path.join(folder_path, "dataset.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["title"] = data.get("title")
            # NOTE: licence_ids is for relationship, not a db field
            metadata["licence_uids"] = data.get("licences")
            metadata["publication_date"] = data.get("publication_date")
            metadata["resource_update"] = data.get("update_date")
            if "eqc" in data:
                metadata["use_eqc"] = data["eqc"]
    if "documentation.yaml" in file_names:
        with open(os.path.join(folder_path, "documentation.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["documentation"] = data.get("documentation")
    for candidate_name in ["overview.png", "overview.jpg"]:
        if candidate_name in file_names:
            metadata["previewimage"] = os.path.abspath(
                os.path.join(folder_path, candidate_name)
            )
    for file_name, db_field_name in [
        ("form.json", "form"),
        ("constraints.json", "constraints"),
    ]:
        if file_name in file_names:
            metadata[db_field_name] = os.path.abspath(
                os.path.join(folder_path, file_name)
            )
    metadata["references"] = []
    if "references.yaml" in file_names:
        with open(os.path.join(folder_path, "references.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            for data_item in data.get("references", []):
                reference_item = {
                    "title": data_item["title"],
                    "content": None,
                    "copy": data_item.get("copy"),
                    "url": None,
                    "download_file": None,
                }
                content_file_name = data_item["content"]
                if content_file_name and content_file_name in file_names:
                    reference_item["content"] = os.path.abspath(
                        os.path.join(folder_path, content_file_name)
                    )
                else:
                    print("warning: reference to item %r not found" % content_file_name)
                    continue
                download_file_name = data_item.get("filename")
                if download_file_name and download_file_name in file_names:
                    reference_item["download_file"] = os.path.abspath(
                        os.path.join(folder_path, download_file_name)
                    )
                metadata["references"].append(reference_item)
    if "metadata.yaml" in file_names:
        with open(os.path.join(folder_path, "metadata.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["type"] = data.get("resource_type")
            metadata["doi"] = data.get("doi")
    return metadata


def store_licences(
    session_obj: sessionmaker | None,
    licences: list[Any],
    doc_storage_path: str | pathlib.Path | None = None,
) -> list[dict[str, Any]]:
    """Store a list of licences in a database and in the document storage path.

    Store a list of licences (as returned by `load_licences_from_folder`)
    in a database and in the document storage path.
    If `doc_storage_path` is None, it will take DOCUMENT_STORAGE from the environment.

    Parameters
    ----------
    session_obj: Session sqlalchemy object
    licences: list of licences (as returned by `load_licences_from_folder`)
    doc_storage_path: base folder path of the document storage

    Returns
    -------
    list: list of dictionaries of records inserted.
    """
    all_stored = []
    session_obj = database.ensure_session_obj(session_obj)
    with session_obj() as session:
        for licence in licences:
            file_path = licence["download_filename"]
            subpath = os.path.join("licences", licence["licence_uid"])
            licence["download_filename"] = save_in_document_storage(
                file_path, doc_storage_path, subpath
            )
            licence_obj = database.Licence(**licence)
            session.add(licence_obj)
            stored_as_dict = object_as_dict(licence_obj)
            all_stored.append(stored_as_dict)
        session.commit()
    return all_stored


def store_dataset(
    session_obj: sessionmaker | None,
    dataset_md: dict[str, Any],
    doc_storage_path: str | pathlib.Path | None = None,
) -> dict[str, Any]:
    """Store a resource in a database and in the document storage path.

    Store a resource (as returned by `load_resource_from_folder`) in a database  and in the
    document storage path and return a dictionary of the record stored.

    Parameters
    ----------
    session_obj: Session sqlalchemy object
    dataset_md: resource dictionary (as returned by `load_resource_from_folder`)
    doc_storage_path: base folder path of the document storage

    Returns
    -------
    dict: a dictionary of the record stored.
    """
    dataset = dataset_md.copy()
    session_obj = database.ensure_session_obj(session_obj)
    with session_obj() as session:
        licence_uids = dataset.pop("licence_uids", [])
        subpath = os.path.join("resources", dataset["resource_uid"])
        doc_storage_fields = ["form", "previewimage", "constraints"]
        for field in doc_storage_fields:
            file_path = dataset[field]
            dataset[field] = save_in_document_storage(
                file_path, doc_storage_path, subpath
            )
        # some fields to storage are inside references
        for reference in dataset["references"]:
            for subfield in ["content", "download_file"]:
                if reference.get(subfield):
                    file_path = reference[subfield]
                    reference[subfield] = save_in_document_storage(
                        file_path, doc_storage_path, subpath
                    )
        dataset.pop("related_resources_keywords")
        dataset_obj = database.Resource(**dataset)
        session.add(dataset_obj)
        for licence_uid in licence_uids:
            licence_obj = (
                session.query(database.Licence)
                .filter_by(licence_uid=licence_uid)
                .order_by(database.Licence.revision.desc())
                .first()
            )
            if licence_obj:
                dataset_obj.licences.append(licence_obj)  # type: ignore
        stored_as_dict = object_as_dict(dataset_obj)
        session.commit()
    return stored_as_dict


def find_related_resources(
    resources: list[dict[str, Any]]
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return couples of resources related each other.

    Each input resources is a python dictionary as returned by the function
    load_resource_from_folder.
    At the moment the current implementation filters input resources in this way:
     - look for resources with the same (not empty) list of "keywords" metadata
     - look for resources with at least one common element in the "related_resources_keywords"
    It assumes that the relationship is commutative.

    Parameters
    ----------
    resources: list of resources (i.e. python dictionaries of metadata)

    Returns
    -------
    list: list of tuples (res1, res2), when res1 and res2 are related input resources.
    """
    relationships_found = []
    all_possible_relationships = itertools.combinations(resources, 2)
    for (res1, res2) in all_possible_relationships:
        res1_keywords = res1.get("keywords", [])
        res2_keywords = res2.get("keywords", [])
        if set(res1_keywords) == set(res2_keywords) and len(res1_keywords) > 0:
            relationships_found.append((res1, res2))
        res1_rel_res_kws = res1.get("related_resources_keywords", [])
        res2_rel_res_kws = res2.get("related_resources_keywords", [])
        if set(res1_rel_res_kws) & set(res2_rel_res_kws):
            relationships_found.append((res1, res2))
    return relationships_found
