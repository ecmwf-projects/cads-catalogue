"""utility module to load and store contents in the catalogue database."""
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

import json
import os
import pathlib
from typing import Any, List

import sqlalchemy as sa
import structlog

from cads_catalogue import config, database, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
logger = structlog.get_logger(__name__)

OBJECT_STORAGE_UPLOAD_FIELDS = ["layout", "image"]


def content_sync(
    session: sa.orm.session.Session,
    content: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
) -> database.Content:
    """
    Update db record with a content's metadata dictionary.

    Parameters
    ----------
    session: opened SQLAlchemy session
    content: metadata of loaded content
    storage_settings: object with settings to access the object storage

    Returns
    -------
    The created/updated db message
    """
    content = content.copy()
    content_uid = content["content_uid"]
    keywords = content.pop("keywords", [])

    subpath = os.path.join("contents", content["content_uid"])
    for field in OBJECT_STORAGE_UPLOAD_FIELDS:
        file_path = content.get(field)
        if not file_path:
            continue
        content[field] = object_storage.store_file(
            file_path,
            storage_settings.object_storage_url,
            bucket_name=storage_settings.catalogue_bucket,
            subpath=subpath,
            **storage_settings.storage_kws,
        )

    # upsert of the message
    db_content = session.scalars(
        sa.select(database.Content).filter_by(content_uid=content_uid).limit(1)
    ).first()
    if not db_content:
        db_content = database.Content(**content)
        session.add(db_content)
        logger.debug("added db content %r" % content_uid)
    else:
        session.execute(
            sa.update(database.Content)
            .filter_by(content_id=db_content.content_id)
            .values(**content)
        )
        logger.debug("updated db content %r" % content_uid)

    # build related keywords
    db_content.keywords = []  # type: ignore
    for keyword in set(keywords):
        category_name, category_value = [r.strip() for r in keyword.split(":")]
        kw_md = {
            "category_name": category_name,
            "category_value": category_value,
            "keyword_name": keyword,
        }
        keyword_obj = session.scalars(
            sa.select(database.ContentKeyword).filter_by(**kw_md).limit(1)
        ).first()
        if not keyword_obj:
            keyword_obj = database.ContentKeyword(**kw_md)
        db_content.keywords.append(keyword_obj)
    return db_content


def load_content_folder(content_folder: str | pathlib.Path) -> List[dict[str, Any]]:
    """
    Parse folder and returns a list of metadata dictionaries, each one for a content.

    Parameters
    ----------
    content_folder: folder path containing content files

    Returns
    -------
    list of dictionaries of information parsed.
    """
    metadata_file_path = os.path.join(content_folder, "metadata.json")
    with open(metadata_file_path) as fp:
        data = json.load(fp)
    ret_value = []
    for site in data["site"]:
        metadata = {
            "site": site,
            "type": data["resource_type"],
            "content_uid": f"{site}-{data['resource_type']}-{data['id']}",
            "title": data["title"],
            "description": data["abstract"],
            "publication_date": data["publication_date"],
            "content_update": data["update_date"],
            "link": data.get("link"),
            "keywords": data.get("keywords", []),
            "data": data.get("data"),
            # managed below:
            # "image": None,
            # "layout": None,
        }
        for ancillar_file_field in OBJECT_STORAGE_UPLOAD_FIELDS:  # image, layout
            metadata[ancillar_file_field] = None
            rel_path = data.get(ancillar_file_field)
            if rel_path:
                ancillar_file_path = os.path.abspath(
                    os.path.join(content_folder, rel_path)
                )
                if os.path.isfile(ancillar_file_path):
                    metadata[ancillar_file_field] = os.path.abspath(
                        os.path.join(content_folder, rel_path)
                    )
                else:
                    raise ValueError(
                        f"{metadata_file_path} contains reference to {ancillar_file_field} file not found!"
                    )
        ret_value.append(metadata)
    return ret_value


def load_contents(contents_root_folder: str | pathlib.Path) -> List[dict[str, Any]]:
    """
    Load all contents from a folder and return a dictionary of metadata extracted.

    Parameters
    ----------
    contents_root_folder: root path where to look for contents (i.e. cads-contents-json root folder)

    Returns
    -------
    List of found contents parsed.
    """
    loaded_contents = []
    if not os.path.isdir(contents_root_folder):
        logger.warning("not found folder {contents_root_folder}!")
        return []
    exclude_folder_names = [".git"]
    for content_folder_name in sorted(os.listdir(contents_root_folder)):
        if content_folder_name in exclude_folder_names:
            continue
        content_folder = os.path.join(contents_root_folder, content_folder_name)
        if not os.path.isdir(content_folder):
            logger.warning("unknown file %r found" % content_folder)
            continue
        try:
            contents_md = load_content_folder(content_folder)
        except:  # noqa
            logger.exception(
                "failed parsing content in %s, error follows" % content_folder
            )
            continue
        loaded_contents += contents_md
    return loaded_contents


def update_catalogue_contents(
    session: sa.orm.session.Session,
    contents_package_path: str | pathlib.Path,
    storage_settings: config.ObjectStorageSettings,
    remove_orphans: bool = True,
):
    """
    Load metadata of contents from files and sync each content in the db.

    Parameters
    ----------
    session: opened SQLAlchemy session
    contents_package_path: root folder path of the contents package (i.e. cads-contents-json root folder)
    storage_settings: object with settings to access the object storage
    remove_orphans: if True, remove from the database other contents not involved (default True)

    Returns
    -------
    list: list of content uids involved
    """
    contents = load_contents(contents_package_path)
    logger.info(
        "loaded %s contents from folder %s" % (len(contents), contents_package_path)
    )
    involved_content_ids = []
    for content in contents:
        content_uid = content["content_uid"]
        involved_content_ids.append(content_uid)
        try:
            with session.begin_nested():
                content_sync(session, content, storage_settings)
            logger.info("content '%s' db sync successful" % content_uid)
        except Exception:  # noqa
            logger.exception(
                "db sync for content '%s' failed, error follows" % content_uid
            )

    if not remove_orphans:
        return involved_content_ids

    # remove not loaded contents from the db
    contents_to_delete = (
        session.scalars(
            sa.select(database.Content).filter(
                database.Content.content_uid.notin_(involved_content_ids)
            )
        )
        .unique()
        .all()
    )
    for content_to_delete in contents_to_delete:
        content_to_delete.keywords = []
        session.delete(content_to_delete)
        logger.info("removed old content '%s'" % content_to_delete.content_uid)

    return involved_content_ids
