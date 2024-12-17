"""module for entry points."""

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

import os.path
from typing import Any, List, Optional

import cads_common.logging
import sqlalchemy as sa
import structlog
import typer

from cads_catalogue import (
    config,
    contents,
    database,
    licence_manager,
    maintenance,
    manager,
    messages,
    object_storage,
    validations,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
CATALOGUE_DIR = os.path.abspath(os.path.join(THIS_PATH, ".."))
PACKAGE_DIR = os.path.abspath(
    os.path.join(
        CATALOGUE_DIR,
        "..",
    )
)
app = typer.Typer()
logger = structlog.get_logger(__name__)


@app.command()
def validate_licences(licences_folder_path: str) -> None:
    """
    Validate contents as valid licences for the catalogue manager.

    Parameters
    ----------
    licences_folder_path: the root folder where to search dataset subfolders in
    """
    cads_common.logging.logging_configure(format="%(levelname)-7s %(message)s")
    if not os.path.isdir(licences_folder_path):
        raise ValueError("%r is not a folder" % licences_folder_path)
    logger.info(
        f"----starting validations of licences at path {licences_folder_path}----"
    )
    licence_manager.load_licences_from_folder(licences_folder_path)
    print()
    logger.info("----end of licence validations----")


@app.command()
def validate_dataset(resource_folder_path: str) -> None:
    """
    Validate a dataset folder for the catalogue manager.

    Parameters
    ----------
    resource_folder_path: dataset folder path
    """
    cads_common.logging.logging_configure(format="%(levelname)-7s %(message)s")
    if not os.path.isdir(resource_folder_path):
        raise ValueError("%r is not a folder" % resource_folder_path)
    validations.validate_dataset(resource_folder_path)


@app.command()
def validate_datasets(resources_folder_path: str) -> None:
    """
    Explore and report subfolders to validate contents as valid datasets for the catalogue manager.

    Parameters
    ----------
    resources_folder_path: the root folder where to search dataset subfolders in
    """
    cads_common.logging.logging_configure(format="%(levelname)-7s %(message)s")
    if not os.path.isdir(resources_folder_path):
        raise ValueError("%r is not a folder" % resources_folder_path)
    validations.validate_datasets(resources_folder_path)


@app.command()
def force_vacuum(
    connection_string: Optional[str] = None, only_older_than_days: Optional[int] = None
) -> None:
    """
    Force run 'vacuum analyze' on all tables.

    If `only_older_than_days` is not None, running only over tables whose vacuum has not run
    for more than `only_older_than_days` days.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    only_older_than_days: number of days from the last run of autovacuum that triggers the vacuum of the table
    """
    cads_common.logging.structlog_configure()
    cads_common.logging.logging_configure()
    logger.info("starting catalogue db vacuum")
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    # set isolation_level because vacuum cannot be performed inside a transaction block
    engine = sa.create_engine(connection_string, isolation_level="AUTOCOMMIT")
    conn = engine.connect()
    try:
        maintenance.force_vacuum(conn, only_older_than_days)
        logger.info("successfully performed catalogue db vacuum")
    except Exception:  # noqa
        logger.exception("problem during db vacuum, error follows")
    finally:
        conn.close()


@app.command()
def info(connection_string: Optional[str] = None) -> None:
    """Test connection to the database located at URI `connection_string`.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'.
    """
    cads_common.logging.structlog_configure()
    cads_common.logging.logging_configure()
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    connection = engine.connect()
    connection.close()
    logger.info("successfully connected to the catalogue database")


@app.command()
def init_db(connection_string: Optional[str] = None, force: bool = False) -> None:
    """Create the database if not exist and update the structure.

    Parameters
    ----------
    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    :param force: if True, drop the database structure and build again from scratch
    """
    cads_common.logging.structlog_configure()
    cads_common.logging.logging_configure()
    logger.info("starting initialization of catalogue db structure")
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    database.init_database(connection_string, force=force)
    logger.info("successfully created/updated the catalogue db structure")


@app.command()
def update_catalogue(
    overrides_path: Optional[str] = None,
    resources_folder_path: str = os.path.join(PACKAGE_DIR, "cads-forms-json"),
    messages_folder_path: str = os.path.join(PACKAGE_DIR, "cads-messages"),
    licences_folder_path: str = os.path.join(PACKAGE_DIR, "cads-licences"),
    cim_folder_path: str = os.path.join(PACKAGE_DIR, "cads-forms-cim-json"),
    contents_folder_path: str = os.path.join(PACKAGE_DIR, "cads-contents-json"),
    contents_config_path: Optional[str] = None,
    connection_string: Optional[str] = None,
    force: bool = False,
    delete_orphans: bool = True,
    include: List[str] = [],
    exclude: List[str] = [],
    exclude_resources: bool = False,
    exclude_licences: bool = False,
    exclude_messages: bool = False,
    exclude_contents: bool = False,
) -> None:
    """Update the database with the catalogue data.

    Parameters
    ----------
    :param overrides_path: path of the file yaml containing overriding metadata
    :param resources_folder_path: folder containing metadata files for resources (i.e. cads-forms-json)
    :param messages_folder_path: folder containing metadata files for system messages (i.e. cads-messages)
    :param licences_folder_path: folder containing metadata files for licences (i.e. cads-licences)
    :param cim_folder_path: str = folder containing CIM Quality Assessment layouts (i.e. cads-forms-cim-json)
    :param contents_folder_path = folder containing metadata files for contents (i.e. cads-contents-json)
    :param contents_config_path = path of the file yaml containing template variables for contents
    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    :param force: if True, run update regardless input folders has no changes from last update (default False)
    :param delete_orphans: if True, delete resources/licences not involved. False if using include/exclude
    :param include: if specified, pattern for resource uids to include in the update
    :param exclude: if specified, pattern for resource uids to exclude from the update
    :param exclude_resources: if True, do not consider input resources (default False)
    :param exclude_licences: if True, do not consider input licences (default False)
    :param exclude_messages: if True, do not consider input messages (default False)
    :param exclude_contents: if True, do not consider input contents (default False)
    """
    cads_common.logging.structlog_configure()
    cads_common.logging.logging_configure()
    logger.info("start running update of the catalogue")

    # input management
    if not os.path.isdir(resources_folder_path) and not exclude_resources:
        raise ValueError("%r is not a folder" % resources_folder_path)
    if not os.path.isdir(licences_folder_path) and not exclude_licences:
        raise ValueError("%r is not a folder" % licences_folder_path)
    if not os.path.isdir(messages_folder_path) and not exclude_messages:
        raise ValueError("%r is not a folder" % messages_folder_path)
    if not os.path.isdir(contents_folder_path) and not exclude_contents:
        raise ValueError("%r is not a folder" % contents_folder_path)

    # test object storage connection, with a timeout (it may raise an error)
    logger.info("testing connection to object storage")
    storage_settings = config.ensure_storage_settings(config.storagesettings)
    object_storage.test_connection_with_timeout(
        15, storage_settings.object_storage_url, storage_settings.storage_kws
    )

    filter_is_active = bool(
        include
        or exclude
        or exclude_resources
        or exclude_licences
        or exclude_messages
        or exclude_contents
    )
    if filter_is_active:
        if delete_orphans:
            logger.warning(
                "'delete-orphans' has been disabled: include/exclude feature is active"
            )
            delete_orphans = False

    # get db session session maker
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)

    logger.info("checking database structure")
    database.init_database(connection_string)

    paths_db_hash_map = [
        (CATALOGUE_DIR, "catalogue_repo_commit"),
        (resources_folder_path, "metadata_repo_commit"),
        (licences_folder_path, "licence_repo_commit"),
        (messages_folder_path, "message_repo_commit"),
        (cim_folder_path, "cim_repo_commit"),
        (contents_folder_path, "content_repo_commit"),
    ]
    involved_licences = []
    involved_resource_uids = []
    try:
        current_override_md = manager.parse_override_md(overrides_path)
    except Exception:
        logger.exception(f"not parsable {overrides_path}")
        current_override_md = dict()
    try:
        current_contents_config = contents.yaml2context(contents_config_path)
    except Exception:
        logger.exception(f"not parsable {contents_config_path}")
        current_contents_config = dict()
    with session_obj.begin() as session:  # type: ignore
        logger.info("comparing current input files with the ones of the last run")
        current_git_hashes = manager.get_current_git_hashes(
            *[f[0] for f in paths_db_hash_map]
        )
        last_run_status = manager.get_status_of_last_update(
            session,
            *[f[1] for f in paths_db_hash_map],
            "override_md",
            "contents_config",
        )
        last_run_git_hashes = last_run_status[:-2]
        last_run_override_md = last_run_status[-2]
        last_run_contents_config = last_run_status[-1]
        override_changed = current_override_md != last_run_override_md
        contents_config_changed = current_contents_config != last_run_contents_config
        if (
            current_git_hashes == last_run_git_hashes
            and not force
            and None not in current_git_hashes
            and not override_changed
            and not contents_config_changed
        ):
            logger.info(
                "catalogue update skipped: source files have not changed. "
                "Use --force to update anyway."
            )
            return
        # if no git ash, consider repo like it was changed
        this_package_changed = (
            current_git_hashes[0] != last_run_git_hashes[0]
            or current_git_hashes[0] is None
        )
        datasets_changed = (
            current_git_hashes[1] != last_run_git_hashes[1]
            or current_git_hashes[1] is None
        )
        licences_changed = (
            current_git_hashes[2] != last_run_git_hashes[2]
            or current_git_hashes[2] is None
        )
        messages_changed = (
            current_git_hashes[3] != last_run_git_hashes[3]
            or current_git_hashes[3] is None
        )
        cim_forms_changed = (
            current_git_hashes[4] != last_run_git_hashes[4]
            or current_git_hashes[4] is None
        )
        contents_changed = (
            current_git_hashes[5] != last_run_git_hashes[5]
            or current_git_hashes[5] is None
            or contents_config_changed
        )
        if this_package_changed:
            logger.info(
                "detected update of cads-catalogue repository. Imposing automatic --force mode."
            )
            force = True
        if override_changed:
            logger.info(
                "detected update of override information. Imposing automatic --force mode."
            )
            force = True
        # licences
        licences_processed = False
        if not exclude_licences:
            if not licences_changed and not force:
                logger.info(
                    "catalogue update of licences skipped: source files have not changed. "
                    "Use --force to update anyway."
                )
            else:
                licences_processed = True
                logger.info("db updating of licences")
                involved_licences = licence_manager.update_catalogue_licences(
                    session,
                    licences_folder_path,
                    storage_settings,
                )
        # resources
        some_resources_processed = False
        if not exclude_resources:
            if (
                not datasets_changed
                and not force
                and not cim_forms_changed
                and not licences_processed
            ):
                logger.info(
                    "catalogue update of resources skipped: source files have not changed. "
                    "Use --force to update anyway."
                )
            else:
                some_resources_processed = True
                logger.info("db updating of datasets")
                involved_resource_uids = manager.update_catalogue_resources(
                    session,
                    resources_folder_path,
                    cim_folder_path,
                    storage_settings,
                    force=force or licences_processed,
                    include=include,
                    exclude=exclude,
                    override_md=current_override_md,
                )
        # messages
        messages_processed = False
        if not exclude_messages:
            if not some_resources_processed and not messages_changed and not force:
                logger.info(
                    "catalogue update of messages skipped: source files have not changed. "
                    "Use --force to update anyway."
                )
            else:
                messages_processed = True
                logger.info("db updating of messages")
                messages.update_catalogue_messages(session, messages_folder_path)
        # contents
        contents_processed = False
        if not exclude_contents:
            if not contents_changed and not force:
                logger.info(
                    "catalogue update of contents skipped: source files have not changed. "
                    "Use --force to update anyway."
                )
            else:
                contents_processed = True
                logger.info("db updating of contents")
                contents.update_catalogue_contents(
                    session,
                    contents_folder_path,
                    storage_settings,
                    yaml_path=contents_config_path,
                )
        # delete orphans
        if delete_orphans:  # -> always false if filtering is active
            if not exclude_licences and licences_processed:
                logger.info("db removing of orphan licences")
                licence_manager.remove_orphan_licences(
                    session,
                    keep_licences=involved_licences,
                    resources=involved_resource_uids,
                )
            if not exclude_resources and some_resources_processed:
                logger.info("db removing of orphan datasets")
                manager.remove_datasets(
                    session, keep_resource_uids=involved_resource_uids
                )
        # refresh relationships between dataset
        logger.info("db update of relationships between datasets")
        manager.update_related_resources(session)
        # store information of current input status
        status_info: dict[str, Any] = dict()
        if licences_processed:
            # (all) licences have been effectively processed
            status_info["licence_repo_commit"] = current_git_hashes[2]
        if (
            some_resources_processed
            and not include
            and not exclude
            and not exclude_resources
        ):
            # all resources have been effectively processed
            status_info["metadata_repo_commit"] = current_git_hashes[1]
            status_info["cim_repo_commit"] = current_git_hashes[4]
        if messages_processed and not exclude_messages:
            # (all) messages have been effectively processed
            status_info["message_repo_commit"] = current_git_hashes[3]
        if contents_processed and not exclude_contents:
            # (all) contents have been effectively processed
            status_info["content_repo_commit"] = current_git_hashes[5]
        if not status_info:
            logger.info(
                "disabled db update of last commit hashes of source repositories"
            )
        else:
            status_info["catalogue_repo_commit"] = current_git_hashes[0]
            status_info["override_md"] = current_override_md
            status_info["contents_config"] = current_contents_config
            logger.info(
                "db update of inputs' status (git commit hashes and override metadata)"
            )
            manager.update_last_input_status(session, status_info)
        logger.info("end of update of the catalogue")


def main() -> None:
    """Run main catalogue entry points."""
    app()
