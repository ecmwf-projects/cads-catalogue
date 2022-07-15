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
import typer
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists

from cads_catalogue import database, manager

app = typer.Typer()


@app.command()
def info(connection_string: str | None = None) -> None:
    """Test connection to the database located at URI `connection_string`.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'.
    """
    if not connection_string:
        connection_string = database.dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    connection = engine.connect()
    connection.close()
    print("successfully connected to the catalogue database.")


@app.command()
def init_db(connection_string: str | None = None) -> None:
    """Create the database structure.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    if not connection_string:
        connection_string = database.dbsettings.connection_string
    database.init_database(connection_string)
    print("successfully created the catalogue database structure.")


@app.command()
def setup_test_database(
    connection_string: str | None = None, force: bool = False
) -> None:
    """Fill the database with some test data.

    Before to fill with test data:
      - if the database doesn't exist, it creates a new one;
      - if the structure is not updated (or force=True), it builds up the structure from scratch

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    force: if True, create db from scratch also if already existing (default False)
    """
    if not connection_string:
        connection_string = database.dbsettings.connection_string
    engine = sa.create_engine(connection_string)
    structure_exists = True
    if not database_exists(engine.url):
        init_db(connection_string)
    else:
        conn = engine.connect()
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        if set(conn.execute(query).scalars()) != set(database.metadata.tables):  # type: ignore
            structure_exists = False
    if not structure_exists or force:
        init_db(connection_string)

    # load test data
    this_path = os.path.abspath(os.path.dirname(__file__))
    licences_folder_path = os.path.abspath(
        os.path.join(this_path, "../tests/data/cds-licences")
    )
    licences = manager.load_licences_from_folder(licences_folder_path)
    engine = database.init_database(connection_string)
    session_obj = sessionmaker(engine)

    manager.store_licences(session_obj, licences)

    datasets = [
        "reanalysis-era5-land-monthly-means",
        "reanalysis-era5-pressure-levels",
        "reanalysis-era5-land",
    ]
    resources = []
    for dataset in datasets:
        resource_folder_path = os.path.abspath(
            os.path.join(this_path, "../tests/data", dataset)
        )
        resource = manager.load_resource_from_folder(resource_folder_path)
        resources.append(resource)
    related_resources = manager.find_related_resources(resources)
    session = session_obj()
    for resource in resources:
        manager.store_dataset(session_obj, resource)
    for res1, res2 in related_resources:
        res1_obj = (
            session.query(database.Resource)
            .filter_by(resource_uid=res1["resource_uid"])
            .one()
        )
        res2_obj = (
            session.query(database.Resource)
            .filter_by(resource_uid=res2["resource_uid"])
            .one()
        )
        res1_obj.related_resources.append(res2_obj)
        res2_obj.related_resources.append(res1_obj)
    session.commit()
    session.close()


def main() -> None:
    """Run main catalogue entry points."""
    app()
