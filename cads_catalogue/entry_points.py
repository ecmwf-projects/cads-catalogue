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
from typing import Any, Dict, List, Optional

import cads_common.logging
import sqlalchemy as sa
import structlog
import typer
from typer import Option
from typing_extensions import Annotated

from cads_catalogue import (
    config,
    contents,
    database,
    licence_manager,
    maintenance,
    manager,
    messages,
    repos,
    skipping_utils,
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
DEFAULT_RETAIN_SANITY_CHECKS = 10
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
def clone_update_catalogue(
    repo_config_path: str,
    overrides_path: Optional[str] = None,
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
    """Clone source repositories and update the database with the catalogue data.

    Parameters
    ----------
    :param repo_config_path: path of the file yaml containing source repositories to clone
    :param overrides_path: path of the file yaml containing overriding metadata
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
    config_paths = {
        "contents_config_path": contents_config_path,
        "overrides_path": overrides_path,
    }
    filtering_kwargs: Dict[str, Any] = {
        "include": include,
        "exclude": exclude,
        "exclude_resources": exclude_resources,
        "exclude_messages": exclude_messages,
        "exclude_contents": exclude_contents,
        "exclude_licences": exclude_licences,
    }
    repos_info = repos.parse_repos_config(repo_config_path, filtering_kwargs)
    repos_info_cloned = repos.clone_repositories(repos_info, root_path=PACKAGE_DIR)
    input_paths: dict[str, Any] = {
        "resources_folder_path": None,
        "cim_folder_path": None,
        "messages_folder_path": None,
        "licences_folder_path": None,
        "contents_folder_path": None,
    }
    if not exclude_resources:
        input_paths["resources_folder_path"] = [
            r["clone_path"] for r in repos_info_cloned["cads-forms-json"]
        ]
        input_paths["cim_folder_path"] = repos_info_cloned["cads-forms-cim-json"][0][
            "clone_path"
        ]
    if not exclude_messages:
        input_paths["messages_folder_path"] = repos_info_cloned["cads-messages"][0][
            "clone_path"
        ]
    if not exclude_licences:
        input_paths["licences_folder_path"] = repos_info_cloned["cads-licences"][0][
            "clone_path"
        ]
    if not exclude_contents:
        input_paths["contents_folder_path"] = repos_info_cloned["cads-contents-json"][
            0
        ]["clone_path"]
    update_catalogue(
        connection_string=connection_string,
        force=force,
        delete_orphans=delete_orphans,
        **input_paths,  # type: ignore
        **config_paths,  # type: ignore
        **filtering_kwargs,  # type: ignore
    )


@app.command()
def update_catalogue(
    overrides_path: Optional[str] = None,
    resources_folder_path: Annotated[List[str] | None, typer.Option()] = [
        os.path.join(PACKAGE_DIR, "cads-forms-json")
    ],
    messages_folder_path: str | None = os.path.join(PACKAGE_DIR, "cads-messages"),
    licences_folder_path: str | None = os.path.join(PACKAGE_DIR, "cads-licences"),
    cim_folder_path: str | None = os.path.join(PACKAGE_DIR, "cads-forms-cim-json"),
    contents_folder_path: str | None = os.path.join(PACKAGE_DIR, "cads-contents-json"),
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
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    repo_paths = {
        "metadata_repo": resources_folder_path,  # it's a list
        "cim_repo": cim_folder_path,
        "message_repo": messages_folder_path,
        "licence_repo": licences_folder_path,
        "content_repo": contents_folder_path,
    }
    config_paths = {
        "contents_config_path": contents_config_path,
        "overrides_path": overrides_path,
    }
    filtering_kwargs: Dict[str, Any] = {
        "include": include,
        "exclude": exclude,
        "exclude_resources": exclude_resources,
        "exclude_messages": exclude_messages,
        "exclude_contents": exclude_contents,
        "exclude_licences": exclude_licences,
    }
    # preprocessing
    manager.prerun_processing(repo_paths, connection_string, filtering_kwargs)
    # disable delete orphans licences/datasets if filtering is active
    delete_orphans = manager.normalize_delete_orphans(
        delete_orphans, **filtering_kwargs
    )
    # get db session session maker
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)
    # compute skipping logic
    to_process, new_catalogue_update_md, force = skipping_utils.skipping_engine(
        session_obj, config_paths, force, repo_paths, filtering_kwargs
    )
    storage_settings = config.ensure_storage_settings(config.storagesettings)
    with session_obj.begin() as session:  # type: ignore
        if "licences" in to_process:
            logger.info("db updating of licences")
            involved_licences = licence_manager.update_catalogue_licences(
                session,
                licences_folder_path,  # type: ignore
                storage_settings,
            )
        if "datasets" in to_process:
            logger.info("db updating of datasets")
            force_datasets = force or "licences" in to_process
            involved_resource_uids = manager.update_catalogue_resources(
                session,
                resources_folder_path,  # type: ignore
                cim_folder_path,  # type: ignore
                storage_settings,
                force=force_datasets,
                include=include,
                exclude=exclude,
                override_md=new_catalogue_update_md["override_md"],
            )
        if "messages" in to_process:
            logger.info("db updating of messages")
            messages.update_catalogue_messages(session, messages_folder_path)  # type: ignore
        if "contents" in to_process:
            logger.info("db updating of contents")
            contents.update_catalogue_contents(
                session,
                contents_folder_path,  # type: ignore
                storage_settings,
                yaml_path=contents_config_path,
            )
        # delete orphans
        if delete_orphans:  # -> always false if filtering is active
            if "licences" in to_process:
                logger.info("db removing of orphan licences")
                licence_manager.remove_orphan_licences(
                    session,
                    keep_licences=involved_licences,
                    resources=involved_resource_uids,
                )
            if "datasets" in to_process:
                logger.info("db removing of orphan datasets")
                manager.remove_datasets(
                    session, keep_resource_uids=involved_resource_uids
                )

        # refresh relationships between datasets
        if "licences" in to_process or "datasets" in to_process:
            logger.info("db update of relationships between datasets")
            manager.update_related_resources(session)

        # store information of current input status
        if to_process:
            logger.info(
                "db update of inputs' status (git commit hashes and override metadata)"
            )
            manager.update_last_input_status(session, new_catalogue_update_md)
        logger.info("end of update of the catalogue")


@app.command()
def run_sanity_check(
    connection_string: Annotated[
        Optional[str], Option(help="db connection string")
    ] = None,
    retain_only: Annotated[
        int, typer.Option(help="max number of outcomes to store")
    ] = DEFAULT_RETAIN_SANITY_CHECKS,
    url: Annotated[Optional[str], Option(help="API url")] = None,  # noqa: UP007
    key: Annotated[list[str], Option(help="API key(s)")] = [],
    requests_path: Annotated[
        Optional[str],  # noqa: UP007
        Option(
            help="Path to the YAML file with requests to test",
            show_default="random requests",
        ),
    ] = None,
    invalidate_cache: Annotated[
        bool,
        Option(help="Whether to invalidate the cache"),
    ] = True,
    n_jobs: Annotated[
        int,
        Option(help="Number of concurrent requests"),
    ] = 1,
    verbose: Annotated[
        int,
        Option(help="The verbosity level of joblib"),
    ] = 10,
    log_level: Annotated[
        str,
        Option(help="Set the root logger level to the specified level"),
    ] = "INFO",
    regex_pattern: Annotated[
        str,
        Option(help="Regex pattern used to filter collection IDs"),
    ] = r"^(?!test-|provider-).*(?<!-complete)$",
    download: Annotated[
        bool,
        Option(help="Whether to download the results"),
    ] = True,
    cache_key: Annotated[
        str,
        Option(help="Key used to invalidate the cache"),
    ] = "_no_cache",
    n_repeats: Annotated[
        int,
        Option(
            help="Number of times to repeat each request (random requests are regenerated)"
        ),
    ] = 1,
    cyclic: Annotated[
        bool,
        Option(
            help="Whether to repeat requests cyclically ([1, 2, 1, 2]) or not ([1, 1, 2, 2])"
        ),
    ] = True,
    randomise: Annotated[
        bool,
        Option(help="Whether to randomise the order of the requests"),
    ] = False,
    max_runtime: Annotated[
        float | None,
        Option(help="Maximum time (in seconds) each request is allowed to run"),
    ] = None,
    datapi_maximum_tries: Annotated[
        int,
        Option(help="Maximum number of retries"),
    ] = 1,
) -> None:
    """Run e2e sanity checks and store outcomes."""
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)
    logger.info("start running sanity check.")
    manager.run_sanity_check(
        session_obj,
        retain_only,
        url=url,
        keys=key,
        requests_path=requests_path,
        cache_key=cache_key if invalidate_cache else None,
        n_jobs=n_jobs,
        verbose=verbose,
        regex_pattern=regex_pattern,
        download=download,
        n_repeats=n_repeats,
        cyclic=cyclic,
        randomise=randomise,
        max_runtime=max_runtime,
        log_level=log_level,
        maximum_tries=datapi_maximum_tries,
    )
    logger.info("sanity check process completed.")


@app.command()
def update_sanity_check(
    report_path: str,
    connection_string: Optional[str] = None,
    retain_only: int = DEFAULT_RETAIN_SANITY_CHECKS,
) -> None:
    """Update database from a sanity check report file.

    Parameters
    ----------
    :param report_path: path of the json report containing outcomes of sanity check
    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    :param retain_only: number of most recent sanity check info to retain (use negative number for no limit)
    """
    cads_common.logging.structlog_configure()
    cads_common.logging.logging_configure()
    logger.info("start running db update of sanity check information.")
    if not connection_string:
        dbsettings = config.ensure_settings(config.dbsettings)
        connection_string = dbsettings.connection_string
    if not os.path.isfile(report_path):
        logger.error(f"{report_path} not found! No update of sanity check information.")
        return
    engine = sa.create_engine(connection_string)
    session_obj = sa.orm.sessionmaker(engine)
    manager.update_sanity_checks_by_file(session_obj, report_path, retain_only)
    logger.info("db update of sanity check information completed.")


def main() -> None:
    """Run main catalogue entry points."""
    app()
