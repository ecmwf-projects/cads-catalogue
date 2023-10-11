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
    utils,
    validations,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
PACKAGE_DIR = os.path.abspath(os.path.join(THIS_PATH, "..", ".."))
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
    utils.configure_log(logfmt="%(levelname)-7s %(message)s")
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
    utils.configure_log(logfmt="%(levelname)-7s %(message)s")
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
    utils.configure_log(logfmt="%(levelname)-7s %(message)s")
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
    utils.configure_log()
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
    utils.configure_log()
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
    utils.configure_log()
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
    resources: Optional[str] = None,
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
    logger.info("start running update of the catalogue")
    utils.configure_log()
    # input validation
    if not os.path.isdir(resources_folder_path):
        raise ValueError("%r is not a folder" % resources_folder_path)
    if not os.path.isdir(licences_folder_path):
        raise ValueError("%r is not a folder" % licences_folder_path)
    if not os.path.isdir(messages_folder_path):
        raise ValueError("%r is not a folder" % messages_folder_path)

    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)

    # create db if not exists and update the structure
    logger.info("start checking if database structure needs to be updated")
    database.init_database(connection_string)

    # get storage parameters from environment
    storage_settings = config.ensure_storage_settings(config.storagesettings)

    with session_obj.begin() as session:  # type: ignore
        # check if source folders have changed from last registered update
        logger.info("start checking git revision of source files")
        (
            is_db_to_update,
            did_catalogue_repo_change,
            catalogue_hash,
            metadata_hash,
            licence_hash,
            message_hash,
            cim_hash,
        ) = manager.is_db_to_update(
            session,
            resources_folder_path,
            licences_folder_path,
            messages_folder_path,
            cim_folder_path,
        )
        if did_catalogue_repo_change:
            force = True
        if not force and not is_db_to_update:
            logger.info(
                "catalogue update skipped: source files have not changed. "
                "Use --force to update anyway."
            )
            return
        logger.info("start db updating of licences")
        involved_licences = licence_manager.update_catalogue_licences(
            session, licences_folder_path, storage_settings
        )
        logger.info("start db updating of datasets")
        involved_resource_uids = manager.update_catalogue_resources(
            session,
            resources_folder_path,
            cim_folder_path,
            storage_settings,
            force=force,
            resources=resources,
        )
        logger.info("start db updating of messages")
        messages.update_catalogue_messages(session, messages_folder_path)

        if delete_orphans:
            logger.info("start db removing of orphan datasets")
            manager.remove_datasets(session, keep_resource_uids=involved_resource_uids)
        logger.info("start db removing of orphan licences")
        licence_manager.remove_orphan_licences(
            session, keep_licences=involved_licences, resources=involved_resource_uids
        )

        # update hashes from the catalogue_updates table
        logger.info("db update of hash of source repositories")
        session.execute(sa.delete(database.CatalogueUpdate))
        new_update_info = database.CatalogueUpdate(
            catalogue_repo_commit=catalogue_hash,
            metadata_repo_commit=metadata_hash,
            licence_repo_commit=licence_hash,
            message_repo_commit=message_hash,
            cim_repo_commit=cim_hash,
        )
        session.add(new_update_info)
        logger.info(
            "%sdb update with input git hashes: %r, %r, %r, %r, %r"
            % (
                force and "forced " or "",
                catalogue_hash,
                metadata_hash,
                licence_hash,
                message_hash,
                cim_hash,
            )
        )
        logger.info("end of update of the catalogue")


def main() -> None:
    """Run main catalogue entry points."""
    app()
