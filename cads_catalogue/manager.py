"""utility module to load and store data in the catalogue database."""

import datetime

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
from typing import Any, Dict, List, Sequence

import sqlalchemy as sa
import sqlalchemy_utils
import structlog
import yaml
from sqlalchemy.dialects.postgresql import insert

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


def get_git_hashes(folder_map: dict[str, str]) -> Dict[str, str]:
    """
    Return last commit hashes of labelled folders.

    Parameters
    ----------
    folder_map: {'folder_label': 'folder_path'}

    Returns
    -------
    {'folder_label': 'git_hash'}
    """
    current_hashes = dict()
    for folder_label, folder_path in folder_map.items():
        try:
            current_hashes[folder_label] = utils.get_last_commit_hash(folder_path)
        except Exception:  # noqa
            logger.exception(
                f"no check on commit hash for folder '{folder_path}, error follows"
            )
            current_hashes[folder_label] = None
    return current_hashes


def get_status_of_last_update(session: sa.orm.session.Session) -> Dict[str, Any] | None:
    """
    Return last stored git hashes and other information from table catalogue_updates.

    Parameters
    ----------
    session: opened SQLAlchemy session

    Returns
    -------
    The values of input column names for the table catalogue_updates
    """
    last_update_record = session.scalars(
        sa.select(database.CatalogueUpdate)
        .order_by(database.CatalogueUpdate.update_time.desc())
        .limit(1)
    ).first()
    if not last_update_record:
        logger.warning("table catalogue_updates is currently empty")
        return dict()
    ret_value = dict()
    for column in sqlalchemy_utils.get_columns(last_update_record):
        c_name = column.name
        ret_value[c_name] = getattr(last_update_record, c_name)
    return ret_value


def is_resource_to_update(session, resource_folder_paths):
    """Return a tuple (is_to_update, source_hash) to understand if the resource is to update.

    is_to_update is True if input folder has been changed since last update of the datataset, False otherwise;
    source_hash is a hash of the resource_folder_path.

    Parameters
    ----------
    session:
    resource_folder_paths: input folders of the dataset

    Returns
    -------
    True if input folder has changed, False otherwise.
    """
    folders_hash = str(utils.folders2hash(resource_folder_paths).hexdigest())
    # assume resource_uid is the folder name of  resource_folder_paths[0]
    resource_uid = os.path.basename(resource_folder_paths[0].rstrip(os.sep))
    db_resource_hash = session.scalars(
        sa.select(database.Resource.sources_hash)
        .filter_by(resource_uid=resource_uid)
        .limit(1)
    ).first()
    if not db_resource_hash:
        return True, folders_hash
    if folders_hash != db_resource_hash:
        return True, folders_hash
    return False, folders_hash


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
    metadata: dict[str, Any] = dict()
    metadata_file_path = os.path.join(folder_path, "metadata.json")
    if not os.path.isfile(metadata_file_path):
        # some fields are required
        raise ValueError("'metadata.json' not found in %r" % folder_path)
    with open(metadata_file_path) as fp:
        data = json.load(fp)

    metadata["abstract"] = utils.normalize_abstract(data["abstract"])  # required
    metadata["api_enforce_constraints"] = data.get("api_enforce_constraints", False)
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
    metadata["disabled_reason"] = data.get("disabled_reason")
    metadata["doi"] = data.get("doi")
    metadata["ds_contactemail"] = data.get("ds_contactemail")
    metadata["ds_responsible_organisation"] = data.get("ds_responsible_organisation")
    metadata["ds_responsible_organisation_role"] = data.get(
        "ds_responsible_organisation_role"
    )
    end_date = data.get("end_date")
    if end_date == "now":
        metadata["end_date"] = None
    else:
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
    metadata["high_priority_terms"] = data.get("high_priority_terms", "")
    metadata["keywords"] = data.get("keywords", [])

    # NOTE: licence_uids is for relationship, not a db field
    metadata["licence_uids"] = data.get("licences", [])

    metadata["lineage"] = data.get("lineage")
    metadata["popularity"] = data.get("popularity", 1)
    default_public_date = "2017-01-01"
    metadata["publication_date"] = data.get("publication_date")
    if not metadata["publication_date"]:
        logger.warning(
            f"publication_date not provided: setting default '{default_public_date}'"
        )
        metadata["publication_date"] = default_public_date
    metadata["qa_flag"] = data.get("qa_flag", True)
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


def parse_override_md(override_path: str | pathlib.Path | None) -> dict[str, Any]:
    """Parse the input override file and return metadata extracted.

    Metadata returned is meant to override output of load_resource_from_folder for each dataset.

    :param override_path: path to the override.yaml file

    Returns
    -------
    dict: dictionary of metadata extracted
    """
    ret_value: dict[str, Any] = dict()

    # base extraction and validation
    if not override_path:
        return ret_value
    if not os.path.exists(override_path):
        logger.error(f"override file {override_path} not found!")
        return ret_value
    logger.warning(f"detected override file {override_path}")
    with open(override_path) as fp:
        try:
            data = yaml.load(fp.read(), Loader=yaml.loader.BaseLoader)
        except Exception:  # noqa
            logger.exception(f"override file {override_path} is not a valid YAML")
            return ret_value
    if data is None:
        logger.warning(f"override file {override_path} is empty")
        return ret_value
    if not isinstance(data, dict):
        logger.error(
            f"override file {override_path} has a wrong format and cannot be parsed"
        )
        return ret_value

    # normalization
    supported_keys_str = (
        "abstract",
        "begin_date",
        "contactemail",
        "disabled_reason",
        "doi",
        "ds_contactemail",
        "ds_responsible_organisation",
        "ds_responsible_organisation_role",
        "format_version",
        "high_priority_terms",
        "lineage",
        "portal",
        "publication_date",
        "responsible_organisation",
        "responsible_organisation_role",
        "responsible_organisation_website",
        "title",
        "topic",
        "unit_measure",
        "use_limitation",
    )
    supported_keys_bool = (
        "api_enforce_constraints",
        "qa_flag",
        "hidden",
    )
    supported_keys_int = ("popularity",)
    supported_keys_floats = ("representative_fraction",)
    for dataset_uid in data:
        ret_value[dataset_uid] = dict()
        dataset_md = data[dataset_uid]
        if not dataset_md:
            continue
        for key, value in dataset_md.items():
            if value == "null":
                ret_value[dataset_uid][key] = None
                continue
            if key in supported_keys_bool:
                if isinstance(value, bool):
                    ret_value[dataset_uid][key] = value  # type: ignore
                else:
                    ret_value[dataset_uid][key]: bool = utils.str2bool(value)  # type: ignore
            elif key in supported_keys_str:
                ret_value[dataset_uid][key] = value
            elif key in supported_keys_int:
                ret_value[dataset_uid][key] = int(value)
            elif key in supported_keys_floats:
                ret_value[dataset_uid][key] = float(value)
            else:
                logger.warning(
                    f"unknown key '{key}' found in override file for {dataset_uid}. It will be ignored"
                )
                continue
    return ret_value


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


def load_resource_from_folder(
    folder_path: str | pathlib.Path, override_md: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Load metadata of a resource from an input folder.

    Parameters
    ----------
    folder_path: folder path where to collect metadata of a resource
    override_md: dictionary of resource metadata to override

    Returns
    -------
    dict: dictionary of metadata collected
    """
    if override_md is None:
        override_md = dict()
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
    metadata.update(override_md)
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
    # split one-to-one related attributes for building ResourceData
    resource_data_attrs = {
        "adaptor_configuration": dataset.pop("adaptor_configuration"),
        "constraints_data": dataset.pop("constraints_data"),
        "form_data": dataset.pop("form_data"),
        "mapping": dataset.pop("mapping"),
        "resource_uid": dataset["resource_uid"],
    }
    # implementing upsert of resource
    insert_stmt = insert(database.Resource).values(**dataset)
    do_update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["resource_uid"], set_=dataset
    ).returning(database.Resource)
    dataset_obj = session.scalars(
        do_update_stmt, execution_options={"populate_existing": True}
    ).one()
    # implementing upsert of resource_data
    insert_stmt = insert(database.ResourceData).values(**resource_data_attrs)
    do_update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["resource_uid"], set_=resource_data_attrs
    )  # type: ignore
    session.execute(do_update_stmt, execution_options={"populate_existing": True}).all()

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
    Also: B should not be hidden.

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
        if (
            res1_keywords.issubset(res2_keywords)
            and len(res1_keywords) > 0
            # Never create references to hidden resources
            and not res2.hidden
        ):
            relationships_found.append((res1, res2))
            continue
        res1_rel_res_kws = set(res1.related_resources_keywords)
        res2_rel_res_kws = set(res2.related_resources_keywords)
        if (
            res1_rel_res_kws & res2_rel_res_kws
            # Never create references to hidden resources
            and not res2.hidden
        ):
            relationships_found.append((res1, res2))
    return relationships_found


def update_related_resources(session: sa.orm.session.Session):
    """
    Reset and reassign again the relationships between resources.

    Parameters
    ----------
    session: opened SQLAlchemy session

    """
    # could be quite slow
    all_datasets = session.scalars(sa.select(database.Resource)).all()
    # clean related_resources
    for dataset_obj in all_datasets:
        dataset_obj.related_resources = []
        dataset_obj.back_related_resources = []  # type: ignore

    # recompute related resources
    related_resources = find_related_resources(all_datasets)
    for res1, res2 in related_resources:
        res1.related_resources.append(res2)


def prerun_processing(repo_paths, connection_string, filtering_kwargs) -> None:
    """Preliminary processing for the catalogue manager."""
    logger.info("additional input checks")
    for repo_key, filter_key in [
        ("metadata_repo", "exclude_resources"),
        ("cim_repo", "exclude_resources"),
        ("licence_repo", "exclude_licences"),
        ("message_repo", "exclude_messages"),
        ("content_repo", "exclude_contents"),
    ]:
        repo_path = repo_paths[repo_key]
        exclude = filtering_kwargs[filter_key]
        if not os.path.isdir(repo_path) and not exclude:
            raise ValueError(f"'{repo_path}' is not a folder")

    logger.info("updating database structure")
    database.init_database(connection_string)

    logger.info("testing connection to object storage")
    storage_conn_timeout = 15  # seconds
    storage_settings = config.ensure_storage_settings(config.storagesettings)
    object_storage.test_connection_with_timeout(
        storage_conn_timeout,
        storage_settings.object_storage_url,
        storage_settings.storage_kws,
    )


def normalize_delete_orphans(
    delete_orphans: bool,
    include: List[str],
    exclude: List[str],
    exclude_resources: bool,
    exclude_licences: bool,
    exclude_messages: bool,
    exclude_contents: bool,
) -> bool:
    """Disable delete_orphans if any filtering is active."""
    filter_is_active = bool(
        include
        or exclude
        or exclude_resources
        or exclude_licences
        or exclude_messages
        or exclude_contents
    )
    if filter_is_active and delete_orphans:
        logger.warning(
            "'delete-orphans' has been disabled: include/exclude feature is active"
        )
        delete_orphans = False
    return delete_orphans


def update_catalogue_resources(
    session: sa.orm.session.Session,
    resources_folder_path: str | pathlib.Path,
    cim_folder_path: str | pathlib.Path,
    storage_settings: config.ObjectStorageSettings,
    force: bool = False,
    include: List[str] = [],
    exclude: List[str] = [],
    override_md: dict[str, Any] = {},
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
    include: list of include patterns for the resource uids
    exclude: list of exclude patterns for the resource uids
    override_md: dictionary of override metadata for resources

    Returns
    -------
    list: list of resource uids involved
    """
    involved_resource_uids = []

    # filtering resource uids
    folders = set(glob.glob(os.path.join(resources_folder_path, "*/")))
    if include:
        folders = set()
        for pattern in include:
            matched = set(glob.glob(os.path.join(resources_folder_path, f"{pattern}/")))
            folders |= matched
    if exclude:
        for pattern in exclude:
            matched = set(glob.glob(os.path.join(resources_folder_path, f"{pattern}/")))
            folders -= matched

    for resource_folder_path in sorted(folders):
        resource_uid = os.path.basename(resource_folder_path.rstrip(os.sep))
        dataset_override_md = override_md.get(resource_uid, dict())
        cim_resource_folder_path = os.path.join(cim_folder_path, resource_uid)
        folders_to_consider_for_hash = [resource_folder_path]
        if os.path.exists(cim_resource_folder_path):
            folders_to_consider_for_hash.append(cim_resource_folder_path)
        logger.debug("parsing folder %s" % resource_folder_path)
        involved_resource_uids.append(resource_uid)
        try:
            with session.begin_nested():
                # NOTE: here the change of dataset's override is not considered because
                # any change of override file however imposes force mode
                to_update, sources_hash = is_resource_to_update(
                    session, folders_to_consider_for_hash
                )
                if not to_update and not force:
                    logger.info(
                        "skip updating of '%s': no change detected" % resource_uid
                    )
                    continue
                resource = load_resource_from_folder(
                    resource_folder_path, dataset_override_md
                )
                resource["sources_hash"] = sources_hash
                logger.info("resource '%s' loaded successful" % resource_uid)
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
            logger.info("resource '%s' db sync successful" % resource_uid)
        except Exception:  # noqa
            logger.exception(
                "db sync for resource '%s' failed, error follows" % resource_uid
            )
    return involved_resource_uids


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
        if dataset_to_delete.resource_data:
            session.delete(dataset_to_delete.resource_data)
        session.delete(dataset_to_delete)
        logger.info("removed resource '%s'" % dataset_to_delete.resource_uid)


def update_last_input_status(
    session: sa.orm.session.Session, status_info: dict[str, Any]
):
    """
    Insert (or update) the record in catalogue_updates according to input dictionary.

    Parameters
    ----------
    session: opened SQLAlchemy session
    status_info: dictionary of record properties
    """
    last_update_record = session.scalars(
        sa.select(database.CatalogueUpdate)
        .order_by(database.CatalogueUpdate.update_time.desc())
        .limit(1)
    ).first()
    if not last_update_record:
        last_update_record = database.CatalogueUpdate(**status_info)
        session.add(last_update_record)
    else:
        status_info["update_time"] = datetime.datetime.now()
        session.execute(sa.update(database.CatalogueUpdate).values(**status_info))
