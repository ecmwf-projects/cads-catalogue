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
import logging
import os
import pathlib
import shutil
import tempfile
import urllib.parse
from typing import Any, List, Tuple

from sqlalchemy.orm.session import Session

from cads_catalogue import config, database, object_storage, utils

logger = logging.getLogger(__name__)
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


def is_db_to_update(
    session: Session,
    resources_folder_path: str | pathlib.Path,
    licences_folder_path: str | pathlib.Path,
) -> Tuple[bool, str | None, str | None]:
    """
    Compare current and last run's status of repo folders and return if the database is to update.

    Parameters
    ----------
    session: opened SQLAlchemy session
    resources_folder_path: the folder path where to look for metadata files of all the resources
    licences_folder_path: the folder path where to look for metadata files of all the licences

    Returns
    -------
    (True or False | hash for resources, hash for licences)
    """
    resource_hash = None
    licence_hash = None
    last_update_record = (
        session.query(database.CatalogueUpdate)
        .order_by(database.CatalogueUpdate.update_time.desc())
        .first()
    )
    try:
        resource_hash = utils.get_last_commit_hash(resources_folder_path)
    except Exception:  # noqa
        logger.exception(
            "no check on commit hash for folder %r, error follows"
            % resources_folder_path
        )
    try:
        licence_hash = utils.get_last_commit_hash(licences_folder_path)
    except Exception:  # noqa
        logger.exception(
            "no check on commit hash for folder %r, error follows"
            % licences_folder_path
        )

    if not last_update_record:
        logger.warning("table catalogue_updates is currently empty")
        is_to_update = True
        return is_to_update, resource_hash, licence_hash

    # last_update_record exists
    last_resource_hash = getattr(last_update_record, "catalogue_repo_commit")
    last_licence_hash = getattr(last_update_record, "licence_repo_commit")
    if (
        last_resource_hash
        and last_resource_hash == resource_hash
        and last_licence_hash
        and last_licence_hash == licence_hash
    ):
        is_to_update = False
    else:
        is_to_update = True
    return is_to_update, resource_hash, licence_hash


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
    try:
        md = load_resource_from_folder(resource_folder_path)
    except:  # noqa
        logger.exception(
            "resource at path %r doesn't seem a valid dataset, error follows"
        )
        return False
    allowed_licence_uids = set([r["licence_uid"] for r in licences])
    resource_licences = set(md["licence_uids"])
    not_found_licences = list(resource_licences - allowed_licence_uids)
    if not_found_licences:
        logger.error(
            "resource at path %r doesn't seem a valid dataset, "
            "not found required licences: %r"
            % (resource_folder_path, not_found_licences)
        )
        return False
    return True


def licence_sync(
    session: Session,
    licence_uid: str,
    licences: list[dict[str, Any]],
    storage_settings: config.ObjectStorageSettings,
) -> database.Licence:
    """
    Compare db record and file of a licence and make them the same.

    Parameters
    ----------
    session: opened SQLAlchemy session
    licence_uid: slag of the licence to sync with the database
    licences: list of metadata of all loaded licences
    storage_settings: object with settings to access the object storage

    Returns
    -------
    The created/updated db licence
    """
    loaded_licences = [r for r in licences if r["licence_uid"] == licence_uid]
    if len(loaded_licences) == 0:
        raise ValueError("not found licence %r in loaded licences" % licence_uid)
    elif len(loaded_licences) > 1:
        raise ValueError(
            "more than 1 licence for slag %r in loaded licences" % licence_uid
        )
    loaded_licence = loaded_licences[0]
    db_licence = (
        session.query(database.Licence)
        .filter_by(licence_uid=licence_uid, revision=loaded_licence["revision"])
        .first()
    )
    if not db_licence:
        db_licence = database.Licence(**loaded_licence)
        session.add(db_licence)
        logger.debug("added db licence %r" % licence_uid)
    else:
        session.query(database.Licence).filter_by(
            licence_id=db_licence.licence_id
        ).update(loaded_licence)
        logger.debug("updated db licence %r" % licence_uid)

    file_path = db_licence.download_filename
    subpath = os.path.join("licences", licence_uid)
    storage_kws = storage_settings.storage_kws
    db_licence.download_filename = object_storage.store_file(
        file_path,
        storage_settings.object_storage_url,
        bucket_name=storage_settings.catalogue_bucket,
        subpath=subpath,
        force=True,
        **storage_kws,
    )[0]
    return db_licence


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
            try:
                json_data = json.load(fp)
                licence = {
                    "licence_uid": json_data["id"],
                    "revision": json_data["revision"],
                    "title": json_data["title"],
                    "download_filename": os.path.abspath(
                        os.path.join(folder_path, json_data["downloadableFilename"])
                    ),
                }
                for key in licence:
                    assert licence[key], "%r is required" % key
            except Exception:  # noqa
                logger.exception(
                    "licence file %r is not compliant: ignored" % json_filepath
                )
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
        ("constraints.json", "constraints_data"),
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
    if "hidden" in data:
        if isinstance(data["hidden"], bool):
            metadata["hidden"] = data["hidden"]
        else:
            metadata["hidden"] = utils.str2bool(data["hidden"])
    else:
        metadata["hidden"] = False
    metadata["keywords"] = data.get("keywords")

    # NOTE: licence_uids is for relationship, not a db field
    metadata["licence_uids"] = data.get("licences", [])

    metadata["lineage"] = data.get("lineage")
    metadata["publication_date"] = data.get("publication_date")
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
    variables: list[dict[str, str]] = []
    for variable_name, properties in variables_data.items():
        variable_item = {
            "label": variable_name,
            "description": properties.get("description"),
            "units": properties.get("units"),
        }
        variables.append(variable_item)
    metadata["variables"] = variables
    return metadata


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
    folder_path = str(folder_path).rstrip(os.sep)
    metadata["resource_uid"] = os.path.basename(folder_path)
    loader_functions = [
        load_resource_for_object_storage,
        load_adaptor_information,
        load_resource_documentation,
        load_resource_metadata_file,
        load_resource_variables,
        load_layout_images_info,
    ]
    for loader_function in loader_functions:
        metadata.update(loader_function(folder_path))
    return metadata


def resource_sync(
    session: Session,
    resource: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
) -> database.Resource:
    """
    Compare db record and file of a resource and make them the same.

    Parameters
    ----------
    session: opened SQLAlchemy session
    resource: metadata of a loaded resource from files
    storage_settings: object with settings to access the object storage

    Returns
    -------
    The created/updated db resource
    """
    dataset = resource.copy()
    licence_uids = dataset.pop("licence_uids", [])
    db_licences = dict()
    for licence_uid in licence_uids:
        licence_obj = (
            session.query(database.Licence)
            .filter_by(licence_uid=licence_uid)
            .order_by(database.Licence.revision.desc())
            .first()
        )
        if not licence_obj:
            raise ValueError("licence_uid = %r not found" % licence_uid)
        db_licences[licence_uid] = licence_obj

    subpath = os.path.join("resources", dataset["resource_uid"])
    object_storage_fields = set(dict(OBJECT_STORAGE_UPLOAD_FILES).values())
    if "layout" in object_storage_fields:
        dataset["layout"] = manage_upload_images_and_layout(
            dataset,
            storage_settings.object_storage_url,
            storage_settings.document_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            **storage_settings.storage_kws,
        )
        object_storage_fields.remove("layout")
        del dataset["layout_images_info"]
    for db_field in object_storage_fields:
        file_path = dataset.get(db_field)
        if not file_path:
            continue
        dataset[db_field] = object_storage.store_file(
            file_path,
            storage_settings.object_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            subpath=subpath,
            force=True,
            **storage_settings.storage_kws,
        )[0]
    dataset_query_obj = session.query(database.Resource).filter_by(
        resource_uid=resource["resource_uid"]
    )
    if not dataset_query_obj.all():
        dataset_obj = database.Resource(**dataset)
        session.add(dataset_obj)
    else:
        dataset_query_obj.update(dataset)
        dataset_obj = dataset_query_obj.one()

    dataset_obj.licences = []  # type: ignore
    for licence_uid in licence_uids:
        dataset_obj.licences.append(db_licences[licence_uid])  # type: ignore

    # clean related_resources
    dataset_obj.related_resources = []  # type: ignore
    dataset_obj.back_related_resources = []  # type: ignore
    all_db_resources = session.query(database.Resource).all()
    # recompute related resources
    related_resources = find_related_resources(
        all_db_resources, only_involving_uid=dataset_obj.resource_uid
    )
    for res1, res2 in related_resources:
        res1.related_resources.append(res2)  # type: ignore
    return dataset_obj


def manage_upload_images_and_layout(
    dataset: dict[str, Any],
    object_storage_url: str,
    doc_storage_url: str,
    bucket_name: str = "cads-catalogue",
    ret_layout_data=False,
    **storage_kws: Any,
) -> str:
    """Upload images referenced in the layout.json and upload a modified json with images' URLs.

    Parameters
    ----------
    dataset: resource dictionary (as returned by `load_resource_from_folder`)
    object_storage_url: endpoint URL of the object storage (for upload)
    doc_storage_url: public endpoint URL of the object storage (for download)
    bucket_name: bucket name of the object storage to use
    ret_layout_data: True only for testing, to return modified json of layout
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    str: URL of the layout.json modified with the uploaded URLs of the images.
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
    if ret_layout_data:
        return layout_data
    return layout_url


def find_related_resources(
    resources: list[database.Resource],
    only_involving_uid=None,
) -> list[tuple[database.Resource, database.Resource]]:
    """Return couples of resources related each other.

    Each input resources is a python dictionary as returned by the function
    load_resource_from_folder.
    Links from a resource A to resource B created this way:
     - B has a (not empty) list of "keywords" metadata completely included in A's keywords
     - B has at least one common element in the "related_resources_keywords"

    Parameters
    ----------
    resources: list of resources
    only_involving_uid: if not None, filter results only involving the specified resource_uid

    Returns
    -------
    list: list of tuples [(res1, res2), ...], where (res1, res2) means: res1 has a link to res2
    """
    relationships_found = []
    all_possible_relationships = itertools.permutations(resources, 2)
    for (res1, res2) in all_possible_relationships:
        if (
            only_involving_uid
            and res1.resource_uid != only_involving_uid
            and res2.resource_uid != only_involving_uid
        ):
            continue
        res1_keywords = set(res1.keywords)  # type: ignore
        res2_keywords = set(res2.keywords)  # type: ignore
        if res1_keywords.issubset(res2_keywords) and len(res1_keywords) > 0:
            relationships_found.append((res1, res2))
            continue
        res1_rel_res_kws = set(res1.related_resources_keywords)  # type: ignore
        res2_rel_res_kws = set(res2.related_resources_keywords)  # type: ignore
        if res1_rel_res_kws & res2_rel_res_kws:
            relationships_found.append((res1, res2))
    return relationships_found
