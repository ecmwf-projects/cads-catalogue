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

import functools
import glob
import itertools
import json
import os
import pathlib
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm.session import Session

from cads_catalogue import database, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TEST_LICENCES_DATA_PATH = os.path.abspath(
    os.path.join(THIS_PATH, "..", "tests", "data", "cds-licences")
)
TEST_RESOURCES_DATA_PATH = os.path.abspath(
    os.path.join(THIS_PATH, "..", "tests", "data", "cads-forms-json")
)
OBJECT_STORAGE_UPLOAD_FILES = [
    # (file_name, "db_field_name),
    ("constraints.json", "constraints"),
    ("form.json", "form"),
    ("layout.json", "layout"),
    ("overview.png", "previewimage"),
]


def recursive_key_search(
    obj, key: str, current_result: list[Any] | None = None
) -> list[Any]:
    """Crowl inside input dictionary/list searching for all keys=key for each dictionary found.

    Note that it does not search inside values of the key found.

    Parameters
    ----------
    obj: input dictionary or list
    key: key to search
    current_result: list of results where aggregate what found on

    Returns
    -------
    list of found values
    """
    if current_result is None:
        current_result = []
    if isinstance(obj, dict):
        for current_key, current_value in obj.items():
            if current_key == key:
                current_result.append(current_value)
            else:
                current_result = recursive_key_search(
                    current_value, key, current_result
                )
    elif isinstance(obj, list):
        for item in obj:
            current_result = recursive_key_search(item, key, current_result)
    return current_result


def object_as_dict(obj: Any) -> dict[str, Any]:
    """Convert a sqlalchemy object in a python dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def is_valid_resource(
    resource_folder_path: str | pathlib.Path, licences: list[dict[str, Any]]
) -> bool:
    """Return True if input folders seems a valid resource folder, False otherwise.

    Parameters
    ----------
    resource_folder_path: the folder path where to look for json files of the resource
    licences: list of loaded licences, as returned from `load_licences_from_folder`
    """
    metadata_path = os.path.join(resource_folder_path, "metadata.json")
    if not os.path.isfile(metadata_path):
        return False
    allowed_licence_uids = set([r["licence_uid"] for r in licences])
    resource_licences = set(load_resource_metadata_file(resource_folder_path)["licence_uids"])
    not_found_licences = list(resource_licences - allowed_licence_uids)
    if not_found_licences:
        print("error: not found required licences: %r" % not_found_licences)
        return False
    return True


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


def load_resource_for_object_storage(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load a resource's metadata regarding files that should be uploaded to the object storage.

    Look inside the folder_path tree for files listed in OBJECT_STORAGE_UPLOAD_FILES.
    Actually metadata collected is the absolute path of the files to be uploaded.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata = dict()
    exclude_dirs = ["geco-config"]
    for root, dirs, files in os.walk(folder_path):
        if root in exclude_dirs:
            continue
        found_file_names = list(
            set(files) & set(dict(OBJECT_STORAGE_UPLOAD_FILES).keys())
        )
        for found_file_name in found_file_names:
            db_field_name = dict(OBJECT_STORAGE_UPLOAD_FILES)[found_file_name]
            metadata[db_field_name] = os.path.abspath(
                os.path.join(root, found_file_name)
            )
    return metadata


def load_variable_id_map(form_json_path: str, mapping_json_path: str) -> dict[str, str]:
    """
    Return a dictionary {variable_label: variable_id} parsing form.json and mapping.json.

    Parameters
    ----------
    form_json_path: path to the form.json file
    mapping_json_path: path to the mapping.json file

    Returns
    -------
    a dictionary {variable_label: variable_id}
    """
    ret_value: dict[str, str] = dict()
    if not os.path.isfile(form_json_path) or not os.path.isfile(mapping_json_path):
        return ret_value
    # mapping.json is used to find the list of variable ids
    with open(mapping_json_path) as fp:
        mapping = json.load(fp)
        variable_ids = list(mapping["remap"]["variable"].keys())

    with open(form_json_path) as fp:
        form_data = json.load(fp)
    # inside form.json we can find more keys 'labels' with id-value mappings
    search_results = recursive_key_search(form_data, key="labels")
    label_id_map: dict[str, str] = functools.reduce(
        lambda d, src: d.update(src) or d, search_results, {}
    )
    ret_value = {
        value: key for key, value in label_id_map.items() if key in variable_ids
    }
    return ret_value


def load_resource_documentation(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load a resource's documentation metadata.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata: dict[str, Any] = dict()
    metadata["documentation"] = []
    doc_file_path = os.path.join(folder_path, "documentation.json")
    if not os.path.isfile(doc_file_path):
        return metadata
    with open(doc_file_path) as fp:
        data = json.load(fp)
        metadata["documentation"] = data or []
    return metadata


def load_adaptor_information(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load a resource's adaptor metadata.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata = dict()
    json_files_db_map = [
        ("adaptor.json", "adaptor_configuration"),
        ("form.json", "form_data"),
        ("mapping.json", "mapping"),
    ]
    for file_name, db_field in json_files_db_map:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path) as fp:
                metadata[db_field] = json.load(fp)

    adaptor_code_path = os.path.join(folder_path, "adaptor.py")
    if os.path.isfile(adaptor_code_path):
        with open(adaptor_code_path) as fp:
            metadata["adaptor"] = fp.read()
    return metadata


def load_resource_metadata_file(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load a resource's metadata from the metadata.json file.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata = dict()
    metadata_file_path = os.path.join(folder_path, "metadata.json")
    if not os.path.isfile(metadata_file_path):
        # some fields are required
        raise ValueError("'metadata.json' not found in %r" % folder_path)
    with open(metadata_file_path) as fp:
        data = json.load(fp)

    metadata["abstract"] = data["abstract"]  # required
    metadata["begin_date"] = data.get("begin_date")
    metadata["citation"] = data.get("citation")
    metadata["contactemail"] = data.get("contactemail")
    metadata["description"] = []
    for key, value in data.get("description", dict()).items():
        item = {
            "id": key,
            "label": key.replace("-", " ").capitalize(),
            "value": value,
        }
        metadata["description"].append(item)
    metadata["doi"] = data.get("doi")
    metadata["ds_contactemail"] = data.get("ds_contactemail")
    metadata["ds_responsible_organisation"] = data.get("ds_responsible_organisation")
    metadata["ds_responsible_organisation_role"] = data.get(
        "ds_responsible_organisation_role"
    )
    end_date = data.get("end_date")
    if end_date != "now":
        metadata["end_date"] = end_date
    metadata["file_format"] = data.get("file_format")
    metadata["format_version"] = data.get("format_version")
    bboxes = ("bboxN", "bboxS", "bboxE", "bboxW")
    if [data.get(box) for box in bboxes] == [None] * 4:
        metadata["geo_extent"] = None
    else:
        metadata["geo_extent"] = {
            "bboxN": data.get("bboxN"),
            "bboxS": data.get("bboxS"),
            "bboxE": data.get("bboxE"),
            "bboxW": data.get("bboxW"),
        }
    metadata["keywords"] = data.get("keywords")

    # NOTE: licence_uids is for relationship, not a db field
    metadata["licence_uids"] = data.get("licences", [])

    metadata["lineage"] = data.get("lineage")
    metadata["publication_date"] = data.get("publication_date")

    # NOTE: licence_uids is for relationship, not a db field
    metadata["related_resources_keywords"] = data.get("related_resources_keywords", [])

    metadata["representative_fraction"] = data.get("representative_fraction")
    metadata["responsible_organisation"] = data.get("responsible_organisation")
    metadata["responsible_organisation_role"] = data.get(
        "responsible_organisation_role"
    )
    metadata["responsible_organisation_website"] = data.get(
        "responsible_organisation_website"
    )
    metadata["resource_update"] = data.get("update_date")
    metadata["title"] = data.get("title")
    metadata["topic"] = data.get("topic")
    metadata["type"] = data.get("resource_type")
    metadata["unit_measure"] = data.get("unit_measure")
    metadata["use_limitation"] = data.get("use_limitation")
    return metadata


def load_resource_variables(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load a resource's variables metadata.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata: dict[str, Any] = dict()
    metadata["variables"] = []
    variables_file_path = os.path.join(folder_path, "variables.json")
    if not os.path.isfile(variables_file_path):
        return metadata
    with open(variables_file_path) as fp:
        variables_data = json.load(fp)

    form_json_path = os.path.join(folder_path, "form.json")
    mapping_json_path = os.path.join(folder_path, "mapping.json")
    variable_id_map = load_variable_id_map(form_json_path, mapping_json_path)
    variables: list[dict[str, str]] = []
    for variable_name, properties in variables_data.items():
        variable_item = {
            "id": variable_id_map[variable_name],
            "label": variable_name,
            "description": properties.get("description"),
            "units": properties.get("units"),
        }
        variables.append(variable_item)
    metadata["variables"] = variables
    return metadata


def load_resource_from_folder(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load metadata of a resource from an input folder.

    Actually imported is based on examples provided for reanalysis-era5-land and
    satellite-surface-radiation-budget.

    Parameters
    ----------
    folder_path: folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata: dict[str, Any] = dict()
    metadata["resource_uid"] = os.path.basename(folder_path)
    loader_functions = [
        load_resource_for_object_storage,
        load_adaptor_information,
        load_resource_documentation,
        load_resource_metadata_file,
        load_resource_variables,
    ]
    for loader_function in loader_functions:
        metadata.update(loader_function(folder_path))
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
    _ = dataset.pop("related_resources_keywords", [])
    subpath = os.path.join("resources", dataset["resource_uid"])
    for db_field in set(dict(OBJECT_STORAGE_UPLOAD_FILES).values()):
        file_path = dataset.get(db_field)
        if not file_path:
            continue
        dataset[db_field] = object_storage.store_file(
            file_path,
            object_storage_url,
            subpath=subpath,
            force=True,
            **storage_kws,
        )[0]
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
    Links from a resource A to resource B created this way:
     - B has a (not empty) list of "keywords" metadata completely included in A's keywords
     - B has at least one common element in the "related_resources_keywords"

    Parameters
    ----------
    resources: list of resources (i.e. python dictionaries of metadata)

    Returns
    -------
    list: list of tuples [(res1, res2), ...], where (res1, res2) means: res1 has a link to res2
    """
    relationships_found = []
    all_possible_relationships = itertools.permutations(resources, 2)
    for (res1, res2) in all_possible_relationships:
        res1_keywords = set(res1.get("keywords", []))
        res2_keywords = set(res2.get("keywords", []))
        if res1_keywords.issubset(res2_keywords) and len(res1_keywords) > 0:
            relationships_found.append((res1, res2))
            continue
        res1_rel_res_kws = set(res1.get("related_resources_keywords", []))
        res2_rel_res_kws = set(res2.get("related_resources_keywords", []))
        if res1_rel_res_kws & res2_rel_res_kws:
            relationships_found.append((res1, res2))
    return relationships_found
