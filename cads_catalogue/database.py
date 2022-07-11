"""SQLAlchemy ORM model."""
import os
import typing
from collections import UserDict
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy_utils import create_database, database_exists

metadata = sa.MetaData()
BaseModel = declarative_base(metadata=metadata)


class ResourceLicence(BaseModel):
    """many-to-many ORM model for resources-licences."""

    __tablename__ = "resources_licences"

    resource_id = sa.Column(
        sa.Integer, sa.ForeignKey("resources.resource_id"), primary_key=True
    )
    licence_id = sa.Column(
        sa.Integer, sa.ForeignKey("licences.licence_id"), primary_key=True
    )


related_resources = sa.Table(
    "related_resources",
    metadata,
    sa.Column("related_resource_id", sa.Integer, primary_key=True),
    sa.Column("parent_resource_id", sa.Integer, sa.ForeignKey("resources.resource_id")),
    sa.Column("child_resource_id", sa.Integer, sa.ForeignKey("resources.resource_id")),
)


class Resource(BaseModel):
    """Resource ORM model."""

    __tablename__ = "resources"

    resource_id = sa.Column(sa.Integer, primary_key=True)
    resource_uid = sa.Column(sa.String, index=True, unique=True, nullable=False)
    title = sa.Column(sa.String)
    description = sa.Column(sa.JSON, nullable=False)
    abstract = sa.Column(sa.TEXT, nullable=False)
    contact = sa.Column(sa.ARRAY(sa.VARCHAR(300)))
    form = sa.Column(sa.String)
    constraints = sa.Column(sa.String)
    keywords = sa.Column(sa.ARRAY(sa.VARCHAR(300)))
    version = sa.Column(sa.VARCHAR(300))
    variables = sa.Column(sa.JSON)
    providers = sa.Column(sa.JSON)
    summaries = sa.Column(sa.JSON, nullable=True)
    extent = sa.Column(sa.JSON)
    documentation = sa.Column(sa.JSON)
    type = sa.Column(sa.VARCHAR(300), nullable=False)
    previewimage = sa.Column(sa.String)
    publication_date = sa.Column(sa.DATE)
    record_update = sa.Column(sa.types.DateTime(timezone=True), default=datetime.utcnow)
    references = sa.Column(sa.JSON)
    resource_update = sa.Column(sa.DATE)
    use_eqc = sa.Column(sa.Boolean)

    licences = relationship(
        "Licence", secondary="resources_licences", back_populates="resources"
    )
    related_resources = relationship(
        "Resource",
        secondary=related_resources,
        primaryjoin=resource_id == related_resources.c.child_resource_id,
        secondaryjoin=resource_id == related_resources.c.parent_resource_id,
        backref=backref("back_related_resources"),  # type: ignore
    )


class Licence(BaseModel):
    """Licence ORM model."""

    __tablename__ = "licences"

    licence_id = sa.Column(sa.Integer, primary_key=True)
    licence_uid = sa.Column(sa.String, index=True, nullable=False)
    revision = sa.Column(sa.Integer, index=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    download_filename = sa.Column(sa.String, nullable=False)

    resources = relationship(
        "Resource", secondary="resources_licences", back_populates="licences"
    )

    __table_args__ = (
        UniqueConstraint("licence_uid", "revision", name="licence_uid_revision_uc"),
    )


@typing.no_type_check
def env2postgresq_connection_string(
    env: dict[str, str] | UserDict[str, str] = None
) -> str:
    """Extract postgresql connection string from environment variables.

    Parameters
    ----------
    env: environment to use

    Returns
    -------
    str
        the database connection string
    """
    if not env:
        env = os.environ
    port = env.get("PGPORT", "5432")
    user = env.get("POSTGRES_USER", "")
    psw = env.get("POSTGRES_PASSWORD", "")
    host = env.get("POSTGRES_HOST", "localhost")
    dbname = env.get(" PGDATABASE", user)
    conn_string = f"postgresql://{user}:{psw}@{host}:{port}/{dbname}"
    return conn_string


def init_database(connection_string: str) -> sa.engine.Engine:
    """Create the database (if not existing) and inizialize the structure.

    Parameters
    ----------
    connection_string: something like 'postgresql://user:password@netloc:port/dbname'

    Returns
    -------
    Engine:
        the sqlalchemy engine object
    """
    engine = sa.create_engine(connection_string)
    if not database_exists(engine.url):
        create_database(engine.url)
    # cleanup and create the schema
    metadata.drop_all(engine)
    metadata.create_all(engine)
    return engine
