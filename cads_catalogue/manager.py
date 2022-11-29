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

import datetime
import glob
import itertools
import json
import os
import pathlib
from typing import Any

import yaml
from sqlalchemy import inspect
from sqlalchemy.orm.session import Session

from cads_catalogue import database, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(THIS_PATH, "db_data")


def object_as_dict(obj: Any) -> dict[str, Any]:
    """Convert a sqlalchemy object in a python dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


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


def build_description(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the db field `description` from the yaml data loaded.

    Parameters
    ----------
    data: yaml data

    Returns
    -------
    a list of items of kind {"id": ..., "label": ..., "value": ...}
    """
    ret_value: list[dict[str, str]] = []
    for key, value in data.get("description", dict()).items():
        item = {
            "id": key,
            "label": key.replace("-", " ").capitalize(),
            "value": value,
        }
        ret_value.append(item)
    return ret_value


def load_variable_id_map(form_json_path: str) -> dict[str, str]:
    """
    Return a dictionary {variable_label: variable_id} parsing the form.json file.

    Parameters
    ----------
    form_json_path: path to the form.json file

    Returns
    -------
    a dictionary {variable_label: variable_id}
    """
    if not os.path.isfile(form_json_path):
        return dict()
    with open(form_json_path) as fp:
        form_sections = json.load(fp)
    variable_id_map = dict()
    for form_section in form_sections:
        if "details" in form_section:
            details_section = form_section["details"]
            if "groups" in details_section:
                groups_section = details_section["groups"]
                for group_section in groups_section:
                    if "labels" in group_section:
                        variable_id_map.update(group_section["labels"])
            if "labels" in details_section:
                variable_id_map.update(details_section["labels"])
    variable_id_map = {v: k for k, v in variable_id_map.items()}
    return variable_id_map


def build_variables(
    data: dict[str, Any], variable_id_map=dict | None
) -> list[dict[str, Any]]:
    """Build the db field `variables` from the yaml data loaded.

    Parameters
    ----------
    data: yaml data
    variable_id_map: dictionary to get the variable id from the label

    Returns
    -------
    a list of items of kind {"label": ..., "description": ..., "units": ...}
    """
    if variable_id_map is None:
        variable_id_map = dict()
    ret_value: list[dict[str, str]] = []
    for variable_name, properties in data.get("variables", dict()).items():
        item = {
            "id": variable_id_map[variable_name],
            "label": variable_name,
            "description": properties.get("description"),
            "units": properties.get("units"),
        }
        ret_value.append(item)
    return ret_value


def build_geo_extent(data: dict[str, Any]) -> dict[str, float | None]:
    """Build the db field `geo_extent` from the yaml data loaded.

    Parameters
    ----------
    data: yaml data

    Returns
    -------
    a dictionary of kind {"bboxN": ..., "bboxW": ..., "bboxS": ..., "bboxE": ...}
    """
    yaml_db_keymap = {
        # key_on_yaml: key_on_db_field
        "bboxN": "bboxN",
        "bboxW": "bboxW",
        "bboxS": "bboxS",
        "bboxE": "bboxE",
    }
    geo_extent = dict()
    for key_on_yaml, key_on_db_field in yaml_db_keymap.items():
        geo_extent[key_on_db_field] = data.get(key_on_yaml)
    return geo_extent


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
    variable_id_map = load_variable_id_map(os.path.join(folder_path, "form.json"))
    if "abstract.md" in file_names:
        with open(os.path.join(folder_path, "abstract.md")) as fp:
            metadata["abstract"] = fp.read()
    else:
        # abstract is required
        raise ValueError("'abstract.md' missing in %r" % folder_path)
    if "abstract.yaml" in file_names:
        with open(os.path.join(folder_path, "abstract.yaml")) as fp:
            data = yaml.load(fp, Loader=yaml.loader.SafeLoader)
            metadata["description"] = build_description(data)
            metadata["keywords"] = data.get("keywords")
            metadata["variables"] = build_variables(data, variable_id_map)
            # NOTE: related_resources_keywords is for self-relationship, not a db field
            metadata["related_resources_keywords"] = data.get(
                "related_resources_keywords", []
            )
    if "adaptor.py" in file_names:
        with open(os.path.join(folder_path, "adaptor.py")) as fp:
            metadata["adaptor"] = fp.read()
    if "adaptor_configuration.yaml" in file_names:
        with open(os.path.join(folder_path, "adaptor_configuration.yaml")) as fp:
            metadata["adaptor_configuration"] = yaml.load(
                fp, Loader=yaml.loader.SafeLoader
            )
    if "mapping.json" in file_names:
        with open(os.path.join(folder_path, "mapping.json")) as fp:
            metadata["mapping"] = json.load(fp)
    if "dataset.yaml" in file_names:
        with open(os.path.join(folder_path, "dataset.yaml")) as fp:
            data = yaml.load(fp, Loader=yaml.loader.SafeLoader)
            metadata["title"] = data.get("title")
            # NOTE: licence_ids is for relationship, not a db field
            metadata["licence_uids"] = data.get("licences", [])
            metadata["publication_date"] = data.get("publication_date")
            metadata["resource_update"] = data.get("update_date")
            if "eqc" in data:
                metadata["use_eqc"] = data["eqc"]
    if "documentation.yaml" in file_names:
        with open(os.path.join(folder_path, "documentation.yaml")) as fp:
            data = yaml.load(fp, Loader=yaml.loader.SafeLoader)
    else:
        data = {}
    metadata["documentation"] = data.get("documentation", [])
    for candidate_name in ["overview.png", "overview.jpg"]:
        if candidate_name in file_names:
            metadata["previewimage"] = os.path.abspath(
                os.path.join(folder_path, candidate_name)
            )
    for file_name, db_field_name in [
        ("form.json", "form"),
        ("constraints.json", "constraints"),
        ("layout.json", "layout"),
    ]:
        if file_name in file_names:
            metadata[db_field_name] = os.path.abspath(
                os.path.join(folder_path, file_name)
            )
    metadata["references"] = []
    if "references.yaml" in file_names:
        with open(os.path.join(folder_path, "references.yaml")) as fp:
            data = yaml.load(fp, Loader=yaml.loader.SafeLoader)
            for data_item in data.get("references", []):
                reference_item = {
                    "title": data_item["title"],
                    "content": None,
                    "copy": data_item.get("copy"),
                    "url": data_item.get("url"),
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
            data = yaml.load(fp, Loader=yaml.loader.SafeLoader)
            if "resource_type" not in data:
                raise ValueError("missing key 'resource_type' in metadata.yaml")
            metadata["type"] = data.get("resource_type")
            metadata["doi"] = data.get("doi")
            metadata["geo_extent"] = build_geo_extent(data)
            for field in ("begin_date", "end_date"):
                metadata[field] = data.get(field)
                if isinstance(data.get(field, ""), str) and data.get(
                    field, ""
                ).lower() in ("now", "today", "present"):
                    metadata[field] = datetime.date.today()
            metadata["contact"] = data.get("contactemail")
            if not metadata["publication_date"]:
                # it can be in dataset.yaml
                metadata["publication_date"] = data.get("publication_date")
    else:
        # type is required
        raise ValueError("'metadata.yaml' missing in %r" % folder_path)
    if (
        "variables.yaml" in file_names
    ):  # this overrides if variables were found in abstract.yaml
        with open(os.path.join(folder_path, "variables.yaml")) as fp:
            data = yaml.load(fp, Loader=yaml.loader.SafeLoader)
            metadata["variables"] = build_variables(data, variable_id_map)

    return metadata


def store_licences(
    session: Session,
    licences: list[Any],
    object_storage_url: str,
    **storage_kws: Any,
) -> list[dict[str, Any]]:
    """Store a list of licences in a database and in the object storage.

    Store a list of licences (as returned by `load_licences_from_folder`)
    in a database and in the object storage.
    If `doc_storage_path` is None, it will take DOCUMENT_STORAGE from the environment.

    Parameters
    ----------
    session: opened SQLAlchemy session
    licences: list of licences (as returned by `load_licences_from_folder`)
    object_storage_url: endpoint URL of the object storage
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    list: list of dictionaries of records inserted.
    """
    all_stored = []
    for licence in licences:
        file_path = licence["download_filename"]
        subpath = os.path.join("licences", licence["licence_uid"])
        licence["download_filename"] = object_storage.store_file(
            file_path,
            object_storage_url,
            subpath=subpath,
            force=True,
            **storage_kws,
        )[0]
        licence_obj = database.Licence(**licence)
        session.add(licence_obj)
        stored_as_dict = object_as_dict(licence_obj)
        all_stored.append(stored_as_dict)
    return all_stored


def store_dataset(
    session: Session,
    dataset_md: dict[str, Any],
    object_storage_url: str,
    **storage_kws: Any,
) -> dict[str, Any]:
    """Store a resource in a database and in the object storage.

    Store a resource (as returned by `load_resource_from_folder`) in a database and some of its
    files in the object storage and return a dictionary of the record stored.

    Parameters
    ----------
    session: opened SQLAlchemy session
    dataset_md: resource dictionary (as returned by `load_resource_from_folder`)
    object_storage_url: endpoint URL of the object storage
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    dict: a dictionary of the record stored.
    """
    dataset = dataset_md.copy()
    licence_uids = dataset.pop("licence_uids", [])
    subpath = os.path.join("resources", dataset["resource_uid"])
    obj_storage_fields = ["form", "previewimage", "constraints", "layout"]
    for field in obj_storage_fields:
        file_path = dataset[field]
        dataset[field] = object_storage.store_file(
            file_path,
            object_storage_url,
            subpath=subpath,
            force=True,
            **storage_kws,
        )[0]
    # some fields to storage are inside references
    for reference in dataset["references"]:
        for subfield in ["content", "download_file"]:
            if reference.get(subfield):
                file_path = reference[subfield]
                reference[subfield] = object_storage.store_file(
                    file_path,
                    object_storage_url,
                    subpath=subpath,
                    force=True,
                    **storage_kws,
                )[0]
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
