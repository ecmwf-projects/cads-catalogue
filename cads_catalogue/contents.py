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
import yaml

from cads_catalogue import config, database, layout_manager, object_storage, utils

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
    keywords = content.pop("keywords", [])
    related_datasets = content.pop("related_datasets", [])
    site, ctype, slug = content["site"], content["type"], content["slug"]
    subpath = os.path.join("contents", site, ctype, slug)
    for field in OBJECT_STORAGE_UPLOAD_FIELDS:
        if field == "layout":
            # already done by layout manager
            continue
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

    # upsert of the content
    db_content = session.scalars(
        sa.select(database.Content)
        .filter_by(
            site=site,
            type=ctype,
            slug=slug,
        )
        .limit(1)
    ).first()
    if not db_content:
        db_content = database.Content(**content)
        session.add(db_content)
        logger.debug(f"added content {ctype} '{slug}' for site {site}")
    else:
        session.execute(
            sa.update(database.Content)
            .filter_by(content_id=db_content.content_id)
            .values(**content)
        )
        logger.debug("updated content {ctype} '{slug}' for site {site}")

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

    # build related datasets
    db_content.resources = []  # type: ignore
    for resource_uid in set(related_datasets):
        dataset_obj = session.scalars(
            sa.select(database.Resource).filter_by(resource_uid=resource_uid).limit(1)
        ).first()
        if not dataset_obj:
            logger.warning(
                f"dataset uid '{resource_uid}' not found. "
                f"Skipping relationship with {ctype} '{slug}' for site {site}"
            )
            continue
        db_content.resources.append(dataset_obj)
    return db_content


def load_content_folder(
    content_folder: str | pathlib.Path, global_context: dict[str, Any] | None = None
) -> List[dict[str, Any]] | None:
    """
    Parse folder and returns a list of metadata dictionaries, each one for a content.

    Parameters
    ----------
    content_folder: folder path containing content files
    global_context: dictionary to be used for rendering templates

    Returns
    -------
    list of dictionaries of information parsed.
    """
    if global_context is None:
        global_context = dict()
    metadata_file_path = os.path.join(content_folder, "metadata.json")
    with open(metadata_file_path) as fp:
        data_raw = json.load(fp)
    ret_value = []
    for site in data_raw["site"][:]:
        site_context = global_context.get("default", dict())
        site_context.update(global_context.get(site, dict()))
        data = utils.dict_render(data_raw, site_context)
        metadata = {
            "site": site,
            "type": data["resource_type"],
            "slug": data["id"],
            "title": data["title"],
            "description": data["abstract"],
            "publication_date": data["publication_date"],
            "content_update": data["update_date"],
            "link": data.get("link"),
            "keywords": data.get("keywords", []),
            "related_datasets": data.get("related_datasets", []),
            "data": data.get("data"),
            "hidden": data.get("hidden", False),
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
                    metadata[ancillar_file_field] = ancillar_file_path
                else:
                    raise ValueError(
                        f"{metadata_file_path} contains reference to {ancillar_file_field} file not found!"
                    )
        ret_value.append(metadata)
    return ret_value


def transform_layout(
    content: dict[str, Any],
    storage_settings: config.ObjectStorageSettings,
    global_context: dict[str, Any] | None = None,
):
    """
    Modify layout.json information inside content metadata, with related uploads to the object storage.

    Parameters
    ----------
    content: metadata of a loaded content from files
    storage_settings: object with settings to access the object storage
    global_context: dictionary to be used for rendering templates

    Returns
    -------
    modified version of input resource metadata
    """
    if not content.get("layout"):
        return content
    site, ctype, slug = content["site"], content["type"], content["slug"]
    if global_context is None:
        global_context = dict()
    layout_file_path = content["layout"]
    if not os.path.isfile(layout_file_path):
        return content
    layout_folder_path = os.path.dirname(layout_file_path)
    with open(layout_file_path) as fp:
        layout_data = json.load(fp)
        logger.debug(f"input layout_data: {layout_data}")

    layout_raw_data = layout_manager.transform_html_blocks(
        layout_data, layout_folder_path
    )
    site_context = global_context.get("default", dict())
    site_context.update(global_context.get(site, dict()))
    layout_data = utils.dict_render(layout_raw_data, site_context)
    images_storage_subpath = f"contents/{content['slug']}"
    layout_data = layout_manager.transform_image_blocks(
        layout_data, layout_folder_path, images_storage_subpath, storage_settings
    )
    logger.debug(f"output layout_data: {layout_data}")
    subpath = os.path.join("contents", site, ctype, slug)
    content["layout"] = layout_manager.store_layout_by_data(
        layout_data, content, storage_settings, subpath=subpath
    )
    logger.debug(f"layout url: {content['layout']}")
    return content


def yaml2context(yaml_path: str | pathlib.Path | None) -> dict[str, Any]:
    """
    load yaml used for rendering templates.

    :param yaml_path: yaml path
    :return: yaml parsed
    """
    if not yaml_path:
        logger.info(
            "no selection of a contents configuration file. No variable substitution in templates."
        )
        return dict()
    if not os.path.isfile(yaml_path):
        logger.warning(f"{yaml_path} not found. No variable substitution in templates.")
        return dict()
    logger.info(f"reading contents configuration file {yaml_path}.")
    with open(yaml_path) as fp:
        try:
            data = yaml.load(fp.read(), Loader=yaml.loader.BaseLoader)
        except Exception:
            logger.exception(
                f"{yaml_path} not parsable. No variable substitution in templates."
            )
            return dict()
    return data


def load_contents(
    contents_root_folder: str | pathlib.Path,
    global_context: dict[str, Any] | None = None,
) -> List[dict[str, Any]]:
    """
    Load all contents from a folder and return a dictionary of metadata extracted.

    Parameters
    ----------
    contents_root_folder: root path where to look for contents (i.e. cads-contents-json root folder)
    global_context: dictionary to be used for rendering templates

    Returns
    -------
    List of found contents parsed.
    """
    loaded_contents = []
    if not os.path.isdir(contents_root_folder):
        logger.warning(f"not found folder {contents_root_folder}!")
        return []
    for content_folder_name in sorted(os.listdir(contents_root_folder)):
        content_folder = os.path.join(contents_root_folder, content_folder_name)
        if not os.path.isdir(content_folder):
            logger.warning("unknown file %r found" % content_folder)
            continue
        if not is_a_content_folder(content_folder):
            logger.warning(
                "%r doesn't seem a content folder. Skipping" % content_folder
            )
            continue
        try:
            contents_md = load_content_folder(content_folder, global_context)
        except utils.CADSTemplateKeyError as err:
            logger.error(
                f"rendering of metadata.json failed: {err} "
                f"Content in {content_folder} is not loaded."
            )
            continue
        except Exception:  # noqa
            logger.exception(
                "failed parsing content in %s, error follows" % content_folder
            )
            continue
        if contents_md:
            loaded_contents += contents_md
    return loaded_contents


def update_catalogue_contents(
    session: sa.orm.session.Session,
    contents_package_path: str | pathlib.Path,
    storage_settings: config.ObjectStorageSettings,
    remove_orphans: bool = True,
    yaml_path: str | pathlib.Path | None = None,
):
    """
    Load metadata of contents from files and sync each content in the db.

    Parameters
    ----------
    session: opened SQLAlchemy session
    contents_package_path: root folder path of the contents package (i.e. cads-contents-json root folder)
    storage_settings: object with settings to access the object storage
    remove_orphans: if True, remove from the database other contents not involved (default True)
    yaml_path: path to yaml file containing variables to be rendered in the json files

    Returns
    -------
    list: list of (site, type, slug) of contents involved
    """
    global_context = yaml2context(yaml_path)
    contents = load_contents(contents_package_path, global_context)
    logger.info(
        "loaded %s contents from folder %s" % (len(contents), contents_package_path)
    )
    involved_content_props = []
    for content in contents[:]:
        site, ctype, slug = content["site"], content["type"], content["slug"]
        involved_content_props.append((site, ctype, slug))
        try:
            content = transform_layout(content, storage_settings, global_context)
        except utils.CADSTemplateKeyError as err:
            logger.error(f"Processing layout of content '{slug}' fails: {err}")
            continue
        except Exception:  # noqa
            logger.exception(
                f"Processing layout for content {ctype} '{slug}' for site {site} fails, error follows"
            )
            continue
        try:
            with session.begin_nested():
                content_sync(session, content, storage_settings)
            logger.info(f"content {ctype} '{slug}' for site {site}: db sync successful")
        except Exception:  # noqa
            logger.exception(
                f"db sync for content {ctype} '{slug}' for site {site} failed, error follows"
            )

    if not remove_orphans:
        return involved_content_props

    # remove not loaded contents from the db
    all_db_contents = session.scalars(sa.select(database.Content))
    for db_content in all_db_contents:
        content_props = (db_content.site, db_content.type, db_content.slug)
        if content_props not in involved_content_props:
            db_content.keywords = []
            session.delete(db_content)
            logger.info(
                f"removed old content {content_props[1]} '{content_props[2]}' "
                f"for site {content_props[0]}"
            )

    return involved_content_props


def is_a_content_folder(folder_path: str) -> bool:
    """
    Return True if `folder_path` seems a valid folder of a content resource.

    Parameters
    ----------
    folder_path: folder path of the folder to check.
    """
    exclude_folder_names = [".git"]
    if os.path.basename(folder_path) in exclude_folder_names:
        return False
    if os.path.isfile(os.path.join(folder_path, "metadata.json")):
        return True
    return False
