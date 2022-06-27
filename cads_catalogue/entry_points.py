"""module for entry points"""
import os.path
import subprocess

import sqlalchemy as sa
import typer

from cads_catalogue import database

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
    database.init_db(connection_string)
    print("successfully created the catalogue database structure.")


@app.command()
def load_test_data(connection_string: str) -> None:
    """
    Fill the database with some test data.

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    this_path = os.path.abspath(os.path.dirname(__file__))
    dumped_db_path = os.path.abspath(
        os.path.join(this_path, "../tests/TESTDATA/testdb.sql")
    )
    subprocess.call(["psql", connection_string, "-f", dumped_db_path])
    print("test data loaded.")


def main() -> None:
    """run main catalogue entry points"""
    app()
