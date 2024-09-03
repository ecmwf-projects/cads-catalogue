"""configuration utilities."""
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
    Compare db record and folder of a content and make them the same.

    Parameters
    ----------
    session: opened SQLAlchemy session
    content: metadata of loaded content

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


def load_content_folder(
    content_folder: str | pathlib.Path, site: str, content_type: str
) -> dict[str, Any]:
    """
    Parse a content folder and returns its metadata ready for the database.

    Parameters
    ----------
    content_folder: folder path containing content files
    site: site id of the content
    content_type: type of the content

    Returns
    -------
    dictionary of information parsed.
    """
    folder_name = os.path.basename(content_folder)
    metadata_file_path = os.path.join(content_folder, "metadata.json")
    with open(metadata_file_path) as fp:
        data = json.load(fp)
    metadata = {
        "site": site,
        "type": content_type,
        "content_uid": f"{site}-{content_type}-{folder_name}",
        "link": data.get("link"),
        "title": data["title"],
        "description": data["description"],
        "creation_date": data["published"],
        "last_update": data["updated"],
        "keywords": data.get("keywords", []),
    }
    for ancillar_file_field in OBJECT_STORAGE_UPLOAD_FIELDS:
        metadata[ancillar_file_field] = None
        rel_path = data.get(ancillar_file_field)
        if rel_path:
            ancillar_file_path = os.path.abspath(os.path.join(content_folder, rel_path))
            if os.path.isfile(ancillar_file_path):
                metadata[ancillar_file_field] = os.path.abspath(
                    os.path.join(content_folder, rel_path)
                )
            else:
                raise ValueError(f"file {ancillar_file_path} not found!")
    return metadata


def load_contents(contents_package_path: str | pathlib.Path) -> List[dict[str, Any]]:
    """
    Load all contents from a well-known filesystem root.

    Parameters
    ----------
    contents_package_path: root path where to look for contents (i.e. cads-contents-json root folder)

    Returns
    -------
    List of found contents parsed.
    """
    loaded_contents = []
    contents_root_folder = os.path.join(contents_package_path, "contents")
    if not os.path.isdir(contents_root_folder):
        logger.warning("not found folder {contents_root_folder}!")
        return []
    for site in sorted(os.listdir(contents_root_folder)):
        site_folder = os.path.join(contents_root_folder, site)
        if not os.path.isdir(site_folder):
            logger.warning("unknown file %r found" % site_folder)
            continue
        for content_type in sorted(os.listdir(site_folder)):
            content_type_folder = os.path.join(site_folder, content_type)
            if not os.path.isdir(content_type_folder):
                logger.warning("unknown file %r found" % content_type_folder)
                continue
            for content_folder_name in sorted(os.listdir(content_type_folder)):
                content_folder = os.path.join(content_type_folder, content_folder_name)
                if not os.path.isdir(content_folder):
                    logger.warning("unknown file %r found" % content_folder)
                    continue
                try:
                    content_md = load_content_folder(content_folder, site, content_type)
                except:  # noqa
                    logger.exception(
                        "failed parsing content in %s, error follows"
                        % content_type_folder
                    )
                    continue
                loaded_contents.append(content_md)
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
