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
from typing import Optional

import cads_common.logging
import sqlalchemy as sa
import structlog
import typer

from cads_catalogue import (
    config,
    database,
    licence_manager,
    maintenance,
    manager,
    messages,
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
    resources_folder_path: str = os.path.join(PACKAGE_DIR, "cads-forms-json"),
    messages_folder_path: str = os.path.join(PACKAGE_DIR, "cads-messages"),
    licences_folder_path: str = os.path.join(PACKAGE_DIR, "cads-licences"),
    cim_folder_path: str = os.path.join(PACKAGE_DIR, "cads-forms-cim-json"),
    connection_string: Optional[str] = None,
    force: bool = False,
    delete_orphans: bool = True,
) -> None:
    """Update the database with the catalogue data.

    Before to fill the database:
      - if the database doesn't exist (or some tables are missing), it creates the structure from scratch;
      - check input folders has changes from the last run (if not, and force=False, no update is run)

    Parameters
    ----------
    resources_folder_path: path to the root folder containing metadata files for resources
    messages_folder_path: path to the root folder containing metadata files for system messages
    licences_folder_path: path to the root folder containing metadata files for licences
    cim_folder_path: str = path to the root folder containing CIM generated Quality Assessment layouts
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    force: if True, run update regardless input folders has no changes from last update (default False)
    delete_orphans: if True, delete resources not involved in the update process (default True)
    """
    cads_common.logging.structlog_configure()
    cads_common.logging.logging_configure()
    logger.info("start running update of the catalogue")

    # input validation
    if not os.path.isdir(resources_folder_path):
        raise ValueError("%r is not a folder" % resources_folder_path)
    if not os.path.isdir(licences_folder_path):
        raise ValueError("%r is not a folder" % licences_folder_path)
    if not os.path.isdir(messages_folder_path):
        raise ValueError("%r is not a folder" % messages_folder_path)

    # get db session session maker
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)

    logger.info("checking if database structure needs to be updated")
    database.init_database(connection_string)

    # get storage parameters from environment
    storage_settings = config.ensure_storage_settings(config.storagesettings)

    paths_db_hash_map = [
        (CATALOGUE_DIR, "catalogue_repo_commit"),
        (resources_folder_path, "metadata_repo_commit"),
        (licences_folder_path, "licence_repo_commit"),
        (messages_folder_path, "message_repo_commit"),
        (cim_folder_path, "cim_repo_commit"),
    ]
    with session_obj.begin() as session:  # type: ignore
        logger.info("comparing current git hashes with the ones of the last run")
        current_git_hashes = manager.get_current_git_hashes(
            *[f[0] for f in paths_db_hash_map]
        )
        last_run_git_hashes = manager.get_last_git_hashes(
            session, *[f[1] for f in paths_db_hash_map]
        )
        if current_git_hashes == last_run_git_hashes and not force:
            logger.info(
                "catalogue update skipped: source files have not changed. "
                "Use --force to update anyway."
            )
            return
        if current_git_hashes[0] != last_run_git_hashes[0]:
            logger.info(
                "detected update of cads-catalogue repository. Imposing automatic --force mode."
            )
            force = True

        logger.info("db updating of licences")
        involved_licences = licence_manager.update_catalogue_licences(
            session, licences_folder_path, storage_settings
        )
        logger.info("db updating of datasets")
        involved_resource_uids = manager.update_catalogue_resources(
            session,
            resources_folder_path,
            cim_folder_path,
            storage_settings,
            force=force,
        )
        logger.info("db updating of messages")
        messages.update_catalogue_messages(session, messages_folder_path)
        if delete_orphans:
            logger.info("db removing of orphan datasets")
            manager.remove_datasets(session, keep_resource_uids=involved_resource_uids)
        logger.info("db update of relationships between datasets")
        manager.update_related_resources(session)
        logger.info("db removing of orphan licences")
        licence_manager.remove_orphan_licences(
            session, keep_licences=involved_licences, resources=involved_resource_uids
        )
        # update hashes from the catalogue_updates table
        logger.info("db update of hash of source repositories")
        session.execute(sa.delete(database.CatalogueUpdate))
        new_update_info = database.CatalogueUpdate(
            **dict(
                [(f[1], current_git_hashes[i]) for i, f in enumerate(paths_db_hash_map)]
            )
        )  # type: ignore
        session.add(new_update_info)
        logger.info("end of update of the catalogue")


def main() -> None:
    """Run main catalogue entry points."""
    app()
