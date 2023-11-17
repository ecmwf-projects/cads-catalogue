"""licence processing for the catalogue manager."""

# Copyright 2023, European Union.
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

import collections
import csv
import glob
import json
import os
import pathlib
import shutil
from typing import Any, List

import sqlalchemy as sa
import structlog

from cads_catalogue import config, database, object_storage

logger = structlog.get_logger(__name__)


def licence_sync(
    session: sa.orm.session.Session,
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
    db_licence = session.scalars(
        sa.select(database.Licence)
        .filter_by(licence_uid=licence_uid, revision=loaded_licence["revision"])
        .limit(1)
    ).first()
    if not db_licence:
        db_licence = database.Licence(**loaded_licence)
        session.add(db_licence)
        logger.debug("added db licence %r" % licence_uid)
    else:
        session.execute(
            sa.update(database.Licence)
            .filter_by(licence_id=db_licence.licence_id)
            .values(**loaded_licence)
        )
        logger.debug("updated db licence %r" % licence_uid)

    for column_name in ["download_filename", "md_filename"]:
        file_path = getattr(db_licence, column_name)
        subpath = os.path.join("licences", licence_uid)
        storage_kws = storage_settings.storage_kws
        file_url = object_storage.store_file(
            file_path,
            storage_settings.object_storage_url,  # type: ignore
            bucket_name=storage_settings.catalogue_bucket,  # type: ignore
            subpath=subpath,
            **storage_kws,
        )
        setattr(db_licence, column_name, file_url)
    return db_licence


def load_licence_md(json_filepath: str) -> dict[str, Any] | None:
    """
    Validate and load licence metadata from an input json file.

    Parameters
    ----------
    json_filepath: input json file

    Returns
    -------
    licence metadata extracted or None
    """
    licences_folder = os.path.dirname(json_filepath)
    required_keys = {
        "licence_uid",
        "revision",
        "title",
        "download_filename",
        "md_filename",
        "scope",
    }
    optional_keys = {"portal"}

    if not os.path.isfile(json_filepath):
        return None
    if "deprecated" in os.path.basename(json_filepath).lower():
        logger.warning(
            "licence file %r is deprecated: it will not be loaded" % json_filepath
        )
        return None

    with open(json_filepath) as fp:
        try:
            json_data = json.load(fp)
            assert isinstance(
                json_data, dict
            ), f"json file {json_filepath} must be a dictionary"
        except Exception:  # noqa
            logger.exception(
                "licence file %r not compliant, error follows" % json_filepath
            )
            return None

    found_keys = set(json_data.keys())
    not_found_required = required_keys - found_keys
    if not_found_required:
        logger.error(
            "licence file %r not compliant: required keys not found: %r"
            % (json_filepath, not_found_required)
        )
        return None
    extra_found = found_keys - required_keys - optional_keys
    if extra_found:
        logger.warning(
            "licence file %r has extra keys not used: %r" % (json_filepath, extra_found)
        )

    try:
        licence_md = {
            "licence_uid": json_data["licence_uid"],
            "revision": int(json_data["revision"]),
            "title": json_data["title"],
            "download_filename": os.path.abspath(
                os.path.join(licences_folder, json_data["download_filename"])
            ),
            "md_filename": os.path.abspath(
                os.path.join(licences_folder, json_data["md_filename"])
            ),
            "scope": json_data["scope"],
        }
        for key in licence_md:
            assert licence_md[key], "%r is required" % key
        licence_md["portal"] = json_data.get("portal")
        assert licence_md["scope"] in (
            "dataset",
            "portal",
        ), "scope must be 'dataset' or 'portal'"
        if licence_md["scope"] == "portal":
            assert licence_md[
                "portal"
            ], "when scope is 'portal', key 'portal' is required"
        assert os.path.isfile(
            licence_md["download_filename"]
        ), f"file {licence_md['download_filename']} not found"
        assert os.path.isfile(
            licence_md["md_filename"]
        ), f"file {licence_md['md_filename']} not found"
    except Exception:  # noqa
        logger.exception(
            "licence file %r is not compliant, error follows" % json_filepath
        )
        return None

    return licence_md


def load_licences_from_folder(licences_folder: str) -> List[dict[str, Any]]:
    """
    Load and report from a folder containing licences metadata for the catalogue manager.

    Parameters
    ----------
    licences_folder: the root folder where to search dataset subfolders in
    """
    json_filepaths = glob.glob(os.path.join(licences_folder, "*.json"))
    licences_md: dict[str, Any] = dict()

    for json_filepath in json_filepaths:
        licence_md = load_licence_md(json_filepath)
        if not licence_md:
            continue
        licences_md[json_filepath] = licence_md

    # remove duplicated uid-revision
    duplicated = []
    keys = [(lic["licence_uid"], lic["revision"]) for lic in licences_md.values()]

    for key, occurrences in collections.Counter(keys).items():
        if occurrences > 1:
            paths = [
                k
                for k in licences_md
                if (licences_md[k]["licence_uid"], licences_md[k]["revision"]) == key
            ]
            duplicated += paths
    for path in duplicated:
        logger.error(f"licence file {path} ignored: uid and revision in more files")
        del licences_md[path]

    # remove older revisions
    olders = []
    keys = [lic["licence_uid"] for lic in licences_md.values()]
    for key, occurrences in collections.Counter(keys).items():
        if occurrences > 1:
            paths = [k for k in licences_md if licences_md[k]["licence_uid"] == key]
            max_revision = max([licences_md[p]["revision"] for p in paths])
            for path in paths:
                if licences_md[path]["revision"] != max_revision:
                    olders.append(path)
    for path in olders:
        logger.error(f"licence file {path} ignored: more recent revision already found")
        del licences_md[path]

    return list(licences_md.values())


def update_catalogue_licences(
    session: sa.orm.session.Session,
    licences_folder_path: str,
    storage_settings: config.ObjectStorageSettings,
) -> List[str]:
    """
    Load metadata of licences from files and sync each licence in the db.

    Parameters
    ----------
    session: opened SQLAlchemy session
    licences_folder_path: path to the root folder containing metadata files for licences
    storage_settings: object with settings to access the object storage

    Returns
    -------
    list: list of licence uids involved
    """
    involved_licence_uids = []
    licences = load_licences_from_folder(licences_folder_path)
    logger.info("loaded %s licences from %s" % (len(licences), licences_folder_path))
    for licence in licences:
        licence_uid = licence["licence_uid"]
        involved_licence_uids.append(licence_uid)
        try:
            with session.begin_nested():
                licence_sync(session, licence_uid, licences, storage_settings)
            logger.info("licence '%s' db sync successful" % licence_uid)
        except Exception:  # noqa
            logger.exception(
                "db sync for licence '%s' failed, error follows" % licence_uid
            )
    return involved_licence_uids


def remove_orphan_licences(
    session: sa.orm.session.Session, keep_licences: List[str], resources: List[str]
):
    """
    Remove all licences that not are in the list of `keep_licences` and unrelated to any resource.

    Parameters
    ----------
    session: opened SQLAlchemy session
    keep_licences: list of licence uids to keep
    resources: list of resource_uid
    """
    licences_to_delete = session.scalars(
        sa.select(database.Licence).filter(
            database.Licence.licence_uid.notin_(keep_licences)
        )
    )
    for licence_to_delete in licences_to_delete:
        related_dataset_uids = [r.resource_uid for r in licence_to_delete.resources]  # type: ignore
        if set(related_dataset_uids).intersection(set(resources)):
            continue
        licence_to_delete.resources = []  # type: ignore
        session.delete(licence_to_delete)
        logger.info("removed licence '%s'" % licence_to_delete.licence_uid)


def migrate_from_cds_licences(
    cds_licences_folder: str | pathlib.Path, cads_licences_folder: str | pathlib.Path
) -> None:
    """
    Migrate contents from cds-licences to new repo cads-licences.

    Parameters
    ----------
    cds_licences_folder: cds-licences root folder path
    cads_licences_folder: cads-licences root folder path
    """
    licences: List[dict[str, Any]] = []
    all_input_files = os.listdir(cds_licences_folder)
    json_filepaths = glob.glob(os.path.join(cds_licences_folder, "*.json"))
    for json_filepath in json_filepaths:
        if "deprecated" in os.path.basename(json_filepath).lower():
            logger.warning("licence ignored because deprecated: %r" % json_filepath)
            continue
        with open(json_filepath) as fp:
            try:
                json_data = json.load(fp)
                licence = {
                    "licence_uid": json_data["id"],
                    "revision": int(json_data["revision"]),
                    "title": json_data["title"],
                    "download_filename": json_data["downloadableFilename"],
                }
                assert os.path.isfile(
                    os.path.join(cds_licences_folder, json_data["downloadableFilename"])
                )
                for key in licence:
                    assert licence[key], "%r is required" % key
                licence["scope"] = json_data.get("scope", "dataset")
                if licence["licence_uid"] == "terms-of-use-cds":
                    licence["scope"] = "portal"
                assert licence["scope"] in ("dataset", "portal")
                md_files = [
                    r
                    for r in all_input_files
                    if r.lower().startswith(licence["licence_uid"])
                    and r.lower().endswith(".md")
                ]
                if len(md_files) > 1:
                    logger.warning(
                        "more .md files for licence %s" % licence["licence_uid"]
                    )
                    continue
                if len(md_files) == 1:
                    licence["md_filename"] = md_files[0]
            except Exception:  # noqa
                logger.exception(
                    "licence file %r is not compliant: ignored" % json_filepath
                )
                continue
            already_loaded = [
                (i, r)
                for i, r in enumerate(licences)
                if r["licence_uid"] == licence["licence_uid"]
            ]
            if already_loaded:
                logger.warning(
                    "found multiple licence slags %s in folder %s. Consider to remove the older revisions"
                    % (licence["licence_uid"], cds_licences_folder)
                )
                if already_loaded[0][1]["revision"] < licence["revision"]:
                    licences[already_loaded[0][0]] = licence
            else:
                licences.append(licence)
    for licence in licences:
        licence_uid = licence["licence_uid"]
        json_file_path = os.path.join(cads_licences_folder, licence_uid + ".json")
        with open(json_file_path, "w") as fp:
            json.dump(licence, fp, indent=2)
        shutil.copyfile(
            os.path.join(cds_licences_folder, licence["download_filename"]),
            os.path.join(cads_licences_folder, licence["download_filename"]),
        )
        if licence.get("md_filename"):
            shutil.copyfile(
                os.path.join(cds_licences_folder, licence["md_filename"]),
                os.path.join(cads_licences_folder, licence["md_filename"]),
            )


def export_to_csv(cads_licences_folder: str, csv_path: str) -> None:
    """
    Export (uid, revision, scope) of cads-licences to a csv.

    Parameters
    ----------
    cads_licences_folder: path to the cads-licences folder
    csv_path: csv output file path
    """
    licences = []
    json_filepaths = glob.glob(os.path.join(cads_licences_folder, "*.json"))
    for json_filepath in json_filepaths:
        with open(json_filepath) as fp:
            json_data = json.load(fp)
            licence = {
                "licence_uid": json_data["licence_uid"],
                "revision": json_data["revision"],
                "scope": json_data["scope"],
            }
            if "portal" in json_data:
                licence["portal"] = json_data["portal"]
            licences.append(licence)

    with open(csv_path, "w") as fp:
        writer = csv.DictWriter(
            fp, fieldnames=["licence_uid", "revision", "scope"], delimiter=";"
        )
        writer.writeheader()
        for licence in licences:
            writer.writerow(licence)
