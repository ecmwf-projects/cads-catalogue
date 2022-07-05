"""utility module to load and store data in the catalogue database"""
import glob
import json
import os
import shutil
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import sessionmaker
from yaml.loader import SafeLoader

from cads_catalogue import database


def save_in_document_storage(
    file_path: str | Path, doc_storage_path: str | Path | None = None, subpath: str = ""
) -> str | None:
    """
    Store a file at `file_path` in the document storage, in the path
    <doc_storage_path>/<subpath>/<file_name>
    Return the relative path <subpath>/<file_name> of the file stored. or None if not stored.

    :param file_path: absolute path to the file to store
    :param doc_storage_path: base folder path where to store the file
    :param subpath: optional folder path inside the document storage (created if not existing)
    :return the relative path <subpath>/<file_name> of the file stored.
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
    storage_abs_path = os.path.join(doc_storage_path, storage_rel_path)
    os.makedirs(storage_abs_path, exist_ok=True)
    shutil.copy(file_path, storage_abs_path)
    return storage_rel_path


def load_licences_from_folder(folder_path: str | Path) -> list[dict[str, Any]]:
    """
    Load licences metadata from json files in a folder.

    :param folder_path: the folder path where to look for json files
    :return: list of dictionaries of metadata collected
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


def load_resource_from_folder(folder_path: str | Path) -> dict[str, Any]:
    """
    Load metadata of a resource from a folder.

    :param folder_path: folder path where to collect metadata of a resource
    :return: dictionary of metadata collected
    """
    file_names = os.listdir(folder_path)
    metadata: dict[str, Any] = dict()
    metadata["resource_uid"] = os.path.basename(folder_path)
    metadata["type"] = "dataset"
    if "abstract.md" in file_names:
        with open(os.path.join(folder_path, "abstract.md")) as fp:
            metadata["abstract"] = fp.read()
    if "abstract.yaml" in file_names:
        with open(os.path.join(folder_path, "abstract.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["description"] = json.dumps(data.get("description"))
            metadata["keywords"] = data.get("keywords")
            metadata["variables"] = json.dumps(data.get("variables"))
    if "dataset.yaml" in file_names:
        with open(os.path.join(folder_path, "dataset.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["title"] = data.get("title")
            # NOTE: licence_ids is for relationship, not a db field
            metadata["licence_uids"] = data.get("licences")
            metadata["publication_date"] = data.get("publication_date")
            metadata["resource_update"] = data.get("update_date")
            # metadata["use_eqc"] = data.get('eqc') == 'true'
    if "documentation.yaml" in file_names:
        with open(os.path.join(folder_path, "documentation.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["documentation"] = json.dumps(data.get("documentation"))
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
    # if 'references.yaml' in file_names:
    #     with open(os.path.join(folder_path, 'references.yaml')) as fp:
    #         data = yaml.load(fp, Loader=SafeLoader)
    #         metadata["citation"] = {
    #             'title': data.get('title')
    #         }
    #         content = data.get('content')
    #         if content in file_names:
    #             metadata["citation"]['html'] = fp.read()
    return metadata


def store_licences(
    session_obj: sessionmaker, licences: list[Any], doc_storage_path: str | Path
) -> None:
    """
    Store a list of licences (as returned by `load_licences_from_folder`)
    in a database and in the document storage path.

    :param session_obj: Session sqlalchemy object
    :param licences: list of licences (as returned by `load_licences_from_folder`)
    :param doc_storage_path: base folder path of the document storage
    """
    with session_obj() as session:
        for licence in licences:
            file_path = licence["download_filename"]
            subpath = os.path.join("licences", licence["licence_uid"])
            licence["download_filename"] = save_in_document_storage(
                file_path, doc_storage_path, subpath
            )
            licence_obj = database.Licence(**licence)
            session.add(licence_obj)
        session.commit()


def store_dataset(
    session_obj: sessionmaker, dataset: dict[str, Any], doc_storage_path: str | Path
) -> None:
    """
    Store a list of licences (as returned by `load_resource_from_folder`)
    in a database

    :param session_obj: Session sqlalchemy object
    :param dataset: resource dictionary (as returned by `load_resource_from_folder`)
    :param doc_storage_path: base folder path of the document storage
    """
    with session_obj() as session:
        licence_uids = dataset.pop("licence_uids", [])
        doc_storage_fields = ["form", "previewimage", "constraints"]
        for field in doc_storage_fields:
            file_path = dataset[field]
            subpath = os.path.join("resources", dataset["resource_uid"])
            dataset[field] = save_in_document_storage(
                file_path, doc_storage_path, subpath
            )
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
        session.commit()
