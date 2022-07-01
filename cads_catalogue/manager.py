"""utility module to load and store data in the catalogue database"""
import glob
import json
import os
from typing import Any

import yaml
from sqlalchemy.orm import sessionmaker
from yaml.loader import SafeLoader

from cads_catalogue import database


def load_licences_from_folder(folder_path: str) -> list[dict[str, Any]]:
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
                    "licence_id": json_data["id"],
                    "revision": json_data["revision"],
                    "title": json_data["title"],
                    "download_filename": json_data["downloadableFilename"],
                }
            except KeyError:
                continue
            licences.append(licence)
    return licences


def load_resource_from_folder(folder_path: str) -> dict[str, Any]:
    """
    Load metadata of a resource from a folder.

    :param folder_path: the folder path where to collect metadata of a resource
    :return: dictionary of metadata collected
    """
    file_names = os.listdir(folder_path)
    metadata: dict[str, Any] = dict()
    metadata["resource_id"] = os.path.basename(folder_path)
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
            metadata["licence_ids"] = data.get("licences")
            metadata["publication_date"] = data.get("publication_date")
            metadata["resource_update"] = data.get("update_date")
            # metadata["use_eqc"] = data.get('eqc') == 'true'
    if "documentation.yaml" in file_names:
        with open(os.path.join(folder_path, "documentation.yaml")) as fp:
            data = yaml.load(fp, Loader=SafeLoader)
            metadata["documentation"] = json.dumps(data.get("documentation"))
    if "overview.png" in file_names:
        metadata["previewimage"] = "overview.png"
    if "form.json" in file_names:
        with open(os.path.join(folder_path, "form.json")) as fp:
            metadata["form"] = fp.read()
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


def store_licences(session_obj: sessionmaker, licences: list[Any]) -> None:
    """
    Store a list of licences (as returned by `load_licences_from_folder`)
    in a database

    :param session_obj: Session sqlalchemy object
    :param licences: list of licences (as returned by `load_licences_from_folder`)
    """
    with session_obj() as session:
        for licence_md in licences:
            licence_obj = database.Licence(**licence_md)
            session.add(licence_obj)
        session.commit()
