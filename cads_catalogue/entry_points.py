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

import glob
import logging
import os.path

import sqlalchemy as sa
import sqlalchemy_utils
import typer

from cads_catalogue import config, database, manager

app = typer.Typer()
logger = logging.getLogger(__name__)


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
    logger.info("successfully connected to the catalogue database.")


@app.command()
def init_db(connection_string: str | None = None) -> None:
    """Create the database structure.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    database.init_database(connection_string)
    logger.info("successfully created the catalogue database structure.")


@app.command()
def update_catalogue(
    connection_string: str | None = None,
    force: bool = False,
    resources_folder_path: str = manager.TEST_RESOURCES_DATA_PATH,
    licences_folder_path: str = manager.TEST_LICENCES_DATA_PATH,
    delete_orphans: bool = False,
) -> None:
    """Update the database with the catalogue data.

    Before to fill the database:
      - if the database doesn't exist (or some tables are missing), it creates the structure from scratch;
      - check input folders has changes from the last run (if not, and force=False, no update is run)

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    force: if True, run update regardless input folders has no changes from last update (default False)
    resources_folder_path: path to the root folder containing metadata files for resources
    licences_folder_path: path to the root folder containing metadata files for licences
    delete_orphans: if True, delete resources not involved in the update process (default False)
    """
    # input validation
    if not os.path.isdir(resources_folder_path):
        raise ValueError("%r is not a folder" % resources_folder_path)
    if not os.path.isdir(licences_folder_path):
        raise ValueError("%r is not a folder" % licences_folder_path)

    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)

    # create db/check structure
    must_reset_structure = False
    if not sqlalchemy_utils.database_exists(engine.url):
        logging.info("creating catalogue database")
        sqlalchemy_utils.create_database(engine.url)
        must_reset_structure = True
    else:
        with session_obj.begin() as session:  # type: ignore
            try:
                assert (
                    session.query(database.DBRelease).first().db_release_version
                    == database.DB_VERSION
                )
            except Exception:
                # TODO: exit with error log. User should call manually the init/update db script
                logger.warning(
                    "Catalogue DB structure is not updated. Running the init-db"
                )
                must_reset_structure = True
    if must_reset_structure:
        init_db(connection_string)

    # get storage parameters from environment
    storage_settings = config.ensure_storage_settings(config.storagesettings)

    input_resource_uids = []
    with session_obj.begin() as session:  # type: ignore
        # check if source folders have changed from last registered update
        is_db_to_update, resource_hash, licence_hash = manager.is_db_to_update(
            session, resources_folder_path, licences_folder_path
        )
        if not force and not is_db_to_update:
            logger.info("no manager run: source files didn't change.")
            return

        # load metadata of licences from files and sync each licence in the db
        licences = manager.load_licences_from_folder(licences_folder_path)
        for licence in licences:
            licence_uid = licence["licence_uid"]
            try:
                with session.begin_nested():
                    manager.licence_sync(
                        session, licence_uid, licences, storage_settings
                    )
            except Exception:  # noqa
                logger.exception(
                    "sync for licence %s failed, error follows." % licence_uid
                )

        # load metadata of each resource from files and sync each resource in the db
        for resource_folder_path in glob.glob(
            os.path.join(resources_folder_path, "*/")
        ):
            resource_uid = os.path.basename(resource_folder_path.rstrip(os.sep))
            input_resource_uids.append(resource_uid)
            try:
                with session.begin_nested():
                    resource = manager.load_resource_from_folder(resource_folder_path)
                    manager.resource_sync(session, resource, storage_settings)
            except Exception:  # noqa
                logger.exception(
                    "sync from %s failed, error follows." % resource_folder_path
                )
        # remote not involved resources from the db
        if delete_orphans:
            session.query(database.Resource).filter(
                database.Resource.resource_uid.notin_(input_resource_uids)
            ).delete()

        # update hashes from the catalogue_updates table
        session.query(database.CatalogueUpdate).delete()
        new_update_info = database.CatalogueUpdate(
            catalogue_repo_commit=resource_hash, licence_repo_commit=licence_hash
        )
        session.add(new_update_info)
        logger.info(
            "%supdate catalogue with resources hash: %r and licence hash: %r"
            % (force and "forced " or "", resource_hash, licence_hash)
        )

    # TODO? remove licences from the db if both
    #   * not present in the licences_folder_path
    #   and
    #   * not cited from any dataset


def main() -> None:
    """Run main catalogue entry points."""
    app()
