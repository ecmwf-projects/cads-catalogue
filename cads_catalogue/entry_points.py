"""module for entry points"""

import sqlalchemy as sa
import typer

from cads_catalogue import database

app = typer.Typer()


@app.command()
def info(connection_string: str) -> str:
    """
    Test connection to the database located at URI `connection_string`

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    engine = sa.create_engine(connection_string)
    connection = engine.connect()
    connection.close()
    return "successfully connected to the catalogue database."


@app.command()
def init_db(connection_string: str) -> str:
    """
    Create the database structure

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    database.init_db(connection_string)
    return "successfully created the catalogue database structure."


@app.command()
def load_test_data(connection_string: str) -> str:
    """
    Fill the database with some test data.

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    raise NotImplementedError


def main():
    """run main catalogue entry points"""
    app()
