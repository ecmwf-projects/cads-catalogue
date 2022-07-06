"""module for entry points"""
import os.path

import sqlalchemy as sa
import typer
from sqlalchemy.orm import sessionmaker

from cads_catalogue import database, manager

app = typer.Typer()


@app.command()
def info(connection_string: str) -> None:
    """
    Test connection to the database located at URI `connection_string`

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    engine = sa.create_engine(connection_string)
    connection = engine.connect()
    connection.close()
    print("successfully connected to the catalogue database.")


@app.command()
def init_db(connection_string: str) -> None:
    """
    Create the database structure

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    database.init_database(connection_string)
    print("successfully created the catalogue database structure.")


@app.command()
def load_test_data(connection_string: str) -> None:
    """
    Fill the database with some test data.

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
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
    ]
    session = session_obj()
    for dataset in datasets:
        resource_folder_path = os.path.abspath(
            os.path.join(this_path, "../tests/data", dataset)
        )
        resource = manager.load_resource_from_folder(resource_folder_path)
        manager.store_dataset(session_obj, resource)
    session.close()


def main() -> None:
    """run main catalogue entry points"""
    app()
