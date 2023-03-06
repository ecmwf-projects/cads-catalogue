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

import sqlalchemy as sa
import sqlalchemy_utils
import structlog
import typer

from cads_catalogue import (
    config,
    database,
    licence_manager,
    maintenance,
    manager,
    messages,
)

app = typer.Typer()
logger = structlog.get_logger(__name__)


@app.command()
def force_vacuum(
    connection_string: str | None = None, only_older_than_days: int | None = None
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
def info(connection_string: str | None = None) -> None:
    """Test connection to the database located at URI `connection_string`.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'.
    """
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    connection = engine.connect()
    connection.close()
    logger.info("successfully connected to the catalogue database")


@app.command()
def init_db(connection_string: str | None = None) -> None:
    """Create the database structure.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    logger.info(
        "starting initialization of catalogue db structure (version %s)"
        % database.DB_VERSION
    )
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    database.init_database(connection_string)
    logger.info("successfully created the catalogue db structure")


@app.command()
def update_catalogue(
    resources_folder_path: str = "",  # TODO: remove default
    messages_folder_path: str = "",  # TODO: remove default
    licences_folder_path: str = manager.TEST_LICENCES_DATA_PATH,
    connection_string: str | None = None,
    force: bool = False,
    delete_orphans: bool = False,
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
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    force: if True, run update regardless input folders has no changes from last update (default False)
    delete_orphans: if True, delete resources not involved in the update process (default False)
    """
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

    # create db/check structure
    must_reset_structure = False
    if not sqlalchemy_utils.database_exists(engine.url):
        logger.info("creating catalogue db")
        sqlalchemy_utils.create_database(engine.url)
        must_reset_structure = True
    else:
        with session_obj.begin() as session:  # type: ignore
            try:
                assert (
                    session.query(database.DBRelease).first().db_release_version
                    == database.DB_VERSION
                )
            except Exception:  # noqa
                # TODO: exit with error log. User should call manually the init/update db script
                logger.warning("detected an old catalogue db structure")
                must_reset_structure = True
    if must_reset_structure:
        init_db(connection_string)

    # get storage parameters from environment
    storage_settings = config.ensure_storage_settings(config.storagesettings)

    with session_obj.begin() as session:  # type: ignore
        # check if source folders have changed from last registered update
        (
            is_db_to_update,
            resource_hash,
            licence_hash,
            message_hash,
        ) = manager.is_db_to_update(
            session, resources_folder_path, licences_folder_path, messages_folder_path
        )
        if not force and not is_db_to_update:
            logger.info("catalogue update skipped: source files have not changed")
            return

        licence_manager.update_catalogue_licences(
            session, licences_folder_path, storage_settings
        )
        involved_resource_uids = manager.update_catalogue_resources(
            session, resources_folder_path, storage_settings
        )
        messages.update_catalogue_messages(session, messages_folder_path)

        # remote not involved resources from the db
        if delete_orphans:
            manager.remove_datasets(session, keep_resource_uids=involved_resource_uids)

        # update hashes from the catalogue_updates table
        session.query(database.CatalogueUpdate).delete()
        new_update_info = database.CatalogueUpdate(
            catalogue_repo_commit=resource_hash,
            licence_repo_commit=licence_hash,
            message_repo_commit=message_hash,
        )
        session.add(new_update_info)
        logger.info(
            "%sdb update with input git hashes: %r, %r, %r"
            % (force and "forced " or "", resource_hash, licence_hash, message_hash)
        )

    # TODO? remove licences from the db if both
    #   * not present in the licences_folder_path
    #   and
    #   * not cited from any dataset


def main() -> None:
    """Run main catalogue entry points."""
    app()
