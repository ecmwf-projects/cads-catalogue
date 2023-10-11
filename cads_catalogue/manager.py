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
import hashlib
import itertools
import json
import os
import pathlib
from typing import Any, List, Optional, Sequence, Tuple, Union

import sqlalchemy as sa
import structlog

from cads_catalogue import (
    config,
    database,
    form_manager,
    layout_manager,
    object_storage,
    utils,
)

logger = structlog.get_logger(__name__)
THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TEST_LICENCES_DATA_PATH = os.path.abspath(
    os.path.join(THIS_PATH, "..", "tests", "data", "cds-licences")
)
# form.json and layout.json are managed separately
OBJECT_STORAGE_UPLOAD_FILES = {
    "constraints.json": "constraints",
    "overview.png": "previewimage",
}


def compute_config_hash(resource: dict[str, Any]) -> str:
    """Compute a configuration hash on the basis of some other fields.

    Parameters
    ----------
    resource: dictionary of the resource metadata
    """
    source_fields = [
        "constraints_data",
        "mapping",
        "form_data",
        "adaptor_configuration",
    ]
    ret_value = hashlib.md5()
    for source_field in source_fields:
        field_data = resource.get(source_field)
        if field_data:
            ret_value.update(json.dumps(field_data, sort_keys=True).encode("utf-8"))
    return ret_value.hexdigest()  # type: ignore


def is_db_to_update(
    session: sa.orm.session.Session,
    resources_folder_path: str | pathlib.Path,
    licences_folder_path: str | pathlib.Path,
    messages_folder_path: str | pathlib.Path,
    cim_folder_path: str | pathlib.Path,
) -> Tuple[
    bool,
    bool,
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """
    Compare current and last run's status of repo folders and return information if the database is to update.

    Parameters
    ----------
    session: opened SQLAlchemy session
    resources_folder_path: the folder path where to look for metadata files of all the resources
    licences_folder_path: the folder path where to look for metadata files of all the licences
    messages_folder_path: the folder path where to look for metadata files of all the messages
    cim_folder_path: the folder path containing CIM generated Quality Assessment layouts

    Returns
    -------
    (did_input_folders_change, did_catalogue_source_change, *last_commit_hashes)
    """
    current_hashes = [None, None, None, None, None]

    # load effective commit hashes from the folders
    catalogue_folder_path = os.path.dirname(os.path.abspath(__file__))
    for i, folder_path in enumerate(
        [
            catalogue_folder_path,
            resources_folder_path,
            licences_folder_path,
            messages_folder_path,
            cim_folder_path,
        ]
    ):
        try:
            current_hashes[i] = utils.get_last_commit_hash(folder_path)
        except Exception:  # noqa
            logger.exception(
                "no check on commit hash for folder %r, error follows" % folder_path
            )

    # get last stored commit hashes from the db
    last_hashes = [None, None, None, None, None]
    last_update_record = session.scalars(
        sa.select(database.CatalogueUpdate)
        .order_by(database.CatalogueUpdate.update_time.desc())
        .limit(1)
    ).first()
    if not last_update_record:
        logger.warning("table catalogue_updates is currently empty")
        is_to_update = True
        return is_to_update, True, *current_hashes  # type: ignore
    for i, last_hash_attr in enumerate(
        [
            "catalogue_repo_commit",
            "metadata_repo_commit",
            "licence_repo_commit",
            "message_repo_commit",
            "cim_repo_commit",
        ]
    ):
        last_hashes[i] = getattr(last_update_record, last_hash_attr)

    # logs what's happening
    for i, repo_name in enumerate(
        [
            "catalogue manager",  # cads-catalogue
            "dataset metadata",  # cads-forms-json
            "licence",  # cads-licences
            "message",  # cads-messages
            "cim layouts",  # cads-forms-cim-json
        ]
    ):
        last_hash = last_hashes[i]
        current_hash = current_hashes[i]
        if not last_hash:
            logger.warning("no information of last %s repository commit" % repo_name)
        elif last_hash != current_hash:
            logger.info("detected update of %s repository" % repo_name)

    # set the bool value
    is_to_update = (
        last_hashes == [None, None, None, None, None] or last_hashes != current_hashes
    )
    did_catalogue_source_change = last_hashes[0] != current_hashes[0]
    return is_to_update, did_catalogue_source_change, *current_hashes  # type: ignore


def is_resource_to_update(session, resource_folder_path):
    """Return a tuple (is_to_update, source_hash) to understand if the resource is to update.

    is_to_update is True if input folder has been changed since last update of the datataset, False otherwise;
    source_hash is a hash of the resource_folder_path.

    Parameters
    ----------
    session:
    resource_folder_path: input folder of the dataset

    Returns
    -------
    True if input folder has changed, False otherwise.
    """
    folder_hash = str(utils.folder2hash(resource_folder_path).hexdigest())
    resource_uid = os.path.basename(resource_folder_path.rstrip(os.sep))
    resource_obj = session.scalars(
        sa.select(database.Resource).filter_by(resource_uid=resource_uid).limit(1)
    ).first()
    if not resource_obj:
        return True, folder_hash
    db_resource_hash = resource_obj.sources_hash
    if not db_resource_hash:
        return True, folder_hash
    if folder_hash != db_resource_hash:
        return True, folder_hash
    return False, folder_hash


def load_resource_for_object_storage(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load absolute paths of files that should be uploaded to the object storage.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    metadata = dict()
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename in OBJECT_STORAGE_UPLOAD_FILES and os.path.isfile(file_path):
            db_field_name = OBJECT_STORAGE_UPLOAD_FILES[filename]
            metadata[db_field_name] = os.path.abspath(file_path)
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
    metadata = dict()  # type: ignore
    json_files_db_map = [
        ("adaptor.json", "adaptor_configuration"),
        ("constraints.json", "constraints_data"),
        ("mapping.json", "mapping"),
    ]
    for file_name, db_field in json_files_db_map:
        metadata[db_field] = None
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path) as fp:
                metadata[db_field] = json.load(fp)

    metadata["adaptor"] = None
    adaptor_code_path = os.path.join(folder_path, "adaptor.py")
    if os.path.isfile(adaptor_code_path):
        with open(adaptor_code_path) as fp:
            metadata["adaptor"] = fp.read()
    return metadata


def load_fulltext(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Find a file `fulltext.txt` in order to populate the field `fulltext`.

    Parameters
    ----------
    folder_path: root folder path where to collect metadata of a resource

    Returns
    -------
    dict: dictionary of metadata collected
    """
    # TODO: just a draft
    metadata: dict[str, Any] = dict()
    fulltext_path = os.path.join(folder_path, "fulltext.txt")
    metadata["fulltext"] = None
    if not os.path.isfile(fulltext_path):
        return metadata
    with open(fulltext_path) as fp:
        lines = [r.strip() for r in fp.readlines()]

    # some normalizations
    chars_to_remove = [",", ".", ";", "(", ")"]
    text = " ".join(lines)
    text = text.lower()
    for char_to_remove in chars_to_remove:
        text = text.replace(char_to_remove, " ")

    metadata["fulltext"] = text
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

    metadata["abstract"] = utils.normalize_abstract(data["abstract"])  # required
    metadata["begin_date"] = data.get("begin_date")
    metadata["citation"] = data.get("citation")
    metadata["contactemail"] = data.get("contactemail")
    metadata["description"] = []  # type: ignore
    for key, value in data.get("description", dict()).items():
        item = {
            "id": key,
            "label": key.replace("-", " ").capitalize(),
            "value": value,
        }
        metadata["description"].append(item)  # type: ignore
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
        metadata["geo_extent"] = None  # type: ignore
    else:
        metadata["geo_extent"] = {  # type: ignore
            "bboxN": data.get("bboxN"),
            "bboxS": data.get("bboxS"),
            "bboxE": data.get("bboxE"),
            "bboxW": data.get("bboxW"),
        }
    if "hidden" in data:
        if isinstance(data["hidden"], bool):
            metadata["hidden"] = data["hidden"]  # type: ignore
        else:
            metadata["hidden"]: bool = utils.str2bool(data["hidden"])  # type: ignore
    else:
        metadata["hidden"] = False  # type: ignore
    metadata["keywords"] = data.get("keywords", [])

    # NOTE: licence_uids is for relationship, not a db field
    metadata["licence_uids"] = data.get("licences", [])

    metadata["lineage"] = data.get("lineage")
    default_public_date = "2017-01-01"
    metadata["publication_date"] = data.get("publication_date")
    if not metadata["publication_date"]:
        logger.warning(
            f"publication_date not provided: setting default '{default_public_date}'"
        )
        metadata["publication_date"] = default_public_date
    metadata["qos_tags"] = data.get("qos_tags", [])
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
    if not metadata["resource_update"]:
        logger.warning(
            f"update_date not provided: setting as publication_date '{metadata['publication_date']}'"
        )
        metadata["resource_update"] = metadata["publication_date"]
    metadata["portal"] = data.get("portal", "c3s")
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


def load_resource_from_folder(folder_path: str | pathlib.Path) -> dict[str, Any]:
    """Load metadata of a resource from an input folder.

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
        load_fulltext,
        load_adaptor_information,
        load_resource_documentation,
        load_resource_metadata_file,
        load_resource_variables,
    ]
    for loader_function in loader_functions:
        metadata.update(loader_function(folder_path))
    return metadata


def resource_sync(
    session: sa.orm.session.Session,
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
    keywords = dataset.pop("keywords", [])

    db_licences = dict()
    for licence_uid in licence_uids:
        licence_obj = session.scalars(
            sa.select(database.Licence)
            .filter_by(licence_uid=licence_uid)
            .order_by(database.Licence.revision.desc())
            .limit(1)
        ).first()
        if not licence_obj:
            raise ValueError("licence_uid = %r not found" % licence_uid)
        db_licences[licence_uid] = licence_obj

    subpath = os.path.join("resources", dataset["resource_uid"])
    for _, db_field in OBJECT_STORAGE_UPLOAD_FILES.items():
        file_path = dataset.get(db_field)
        if not file_path:
            continue
        dataset[db_field] = object_storage.store_file(
            file_path,
            storage_settings.object_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            subpath=subpath,
            **storage_settings.storage_kws,
        )
    dataset_query_stmt = sa.select(database.Resource).filter_by(
        resource_uid=resource["resource_uid"]
    )
    dataset_query_obj = session.execute(dataset_query_stmt).scalars().all()
    if not dataset_query_obj:
        dataset_obj = database.Resource(**dataset)
        session.add(dataset_obj)
    else:
        session.execute(
            sa.update(database.Resource)
            .filter_by(resource_uid=resource["resource_uid"])
            .values(**dataset)
        )
        dataset_obj = session.execute(dataset_query_stmt).scalar_one()

    dataset_obj.licences = []  # type: ignore
    for licence_uid in licence_uids:
        dataset_obj.licences.append(db_licences[licence_uid])

    # build again related keywords
    dataset_obj.keywords = []  # type: ignore
    for keyword in set(keywords):
        category_name, category_value = [r.strip() for r in keyword.split(":")]
        kw_md = {
            "category_name": category_name,
            "category_value": category_value,
            "keyword_name": keyword,
        }
        keyword_obj = session.scalars(
            sa.select(database.Keyword).filter_by(**kw_md).limit(1)
        ).first()
        if not keyword_obj:
            keyword_obj = database.Keyword(**kw_md)
        dataset_obj.keywords.append(keyword_obj)

    # clean related_resources
    dataset_obj.related_resources = []
    dataset_obj.back_related_resources = []  # type: ignore
    all_db_resources = session.scalars(sa.select(database.Resource)).all()

    # recompute related resources
    related_resources = find_related_resources(
        all_db_resources, only_involving_uid=dataset_obj.resource_uid
    )
    for res1, res2 in related_resources:
        res1.related_resources.append(res2)

    return dataset_obj


def find_related_resources(
    resources: Sequence[database.Resource],
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
    for res1, res2 in all_possible_relationships:
        if (
            only_involving_uid
            and res1.resource_uid != only_involving_uid
            and res2.resource_uid != only_involving_uid
        ):
            continue
        res1_keywords = set([r.keyword_name for r in res1.keywords])
        res2_keywords = set([r.keyword_name for r in res2.keywords])
        if res1_keywords.issubset(res2_keywords) and len(res1_keywords) > 0:
            relationships_found.append((res1, res2))
            continue
        res1_rel_res_kws = set(res1.related_resources_keywords)
        res2_rel_res_kws = set(res2.related_resources_keywords)
        if res1_rel_res_kws & res2_rel_res_kws:
            relationships_found.append((res1, res2))
    return relationships_found


def update_catalogue_resources(
    session: sa.orm.session.Session,
    resources_folder_path: str | pathlib.Path,
    cim_folder_path: str | pathlib.Path,
    storage_settings: config.ObjectStorageSettings,
    force: bool = False,
    resources: Union[None, str, list] = None
) -> List[str]:
    """
    Load metadata of resources from files and sync each resource in the db.

    Parameters
    ----------
    session: opened SQLAlchemy session
    resources_folder_path: path to the root folder containing metadata files for resources
    storage_settings: object with settings to access the object storage
    cim_folder_path: the folder path containing CIM generated Quality Assessment layouts
    force: if True, no skipping of dataset update based on detected changes of sources is made
    resources: list of resources to update, if not provided then all resources are updated

    Returns
    -------
    list: list of resource uids involved
    """
    input_resource_uids = []

    logger.info("running catalogue db update for resources")
    # load metadata of each resource from files and sync each resource in the db
    if resources is None:
        resources = glob.glob(os.path.join(resources_folder_path, "*/"))
    elif isinstance(resources, str):
        resources = [os.path.join(resources_folder_path, resource)]
    elif isinstance(resource, (list, tuple)):
        resources = [os.path.join(resources_folder_path, resource) for resource in resources]

    for resource_folder_path in resources:
        resource_uid = os.path.basename(resource_folder_path.rstrip(os.sep))
        logger.debug("parsing folder %s" % resource_folder_path)
        input_resource_uids.append(resource_uid)
        try:
            with session.begin_nested():
                to_update, sources_hash = is_resource_to_update(
                    session, resource_folder_path
                )
                if not to_update and not force:
                    logger.info(
                        "resource update %s skipped: no change detected" % resource_uid
                    )
                    continue
                resource = load_resource_from_folder(resource_folder_path)
                resource["sources_hash"] = sources_hash
                logger.info("resource %s loaded successful" % resource_uid)
                resource = layout_manager.transform_layout(
                    session,
                    resource_folder_path,
                    cim_folder_path,
                    resource,
                    storage_settings,
                )
                resource = form_manager.transform_form(
                    session, resource_folder_path, resource, storage_settings
                )
                resource["adaptor_properties_hash"] = compute_config_hash(resource)
                resource_sync(session, resource, storage_settings)
            logger.info("resource %s db sync successful" % resource_uid)
        except Exception:  # noqa
            logger.exception(
                "db sync for resource %s failed, error follows" % resource_uid
            )
    return input_resource_uids


def remove_datasets(session: sa.orm.session.Session, keep_resource_uids: List[str]):
    """
    Remove all datasets that not are in the list of `keep_resource_uids`.

    Parameters
    ----------
    session: opened SQLAlchemy session
    keep_resource_uids: list of uids of resources to save
    """
    # remote not involved resources from the db
    datasets_to_delete = session.scalars(
        sa.select(database.Resource).filter(
            database.Resource.resource_uid.notin_(keep_resource_uids)
        )
    )
    for dataset_to_delete in datasets_to_delete:
        dataset_to_delete.licences = []
        dataset_to_delete.messages = []
        dataset_to_delete.related_resources = []
        session.delete(dataset_to_delete)
        logger.info("removed resource %s" % dataset_to_delete.resource_uid)
