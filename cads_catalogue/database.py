"""SQLAlchemy ORM model"""
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = sa.MetaData()
BaseModel = declarative_base(metadata=metadata)


class ResourceLicence(BaseModel):
    """many-to-many ORM model for resources-licences."""

    __tablename__ = "resources_licences"

    resource_id = sa.Column(
        sa.String, sa.ForeignKey("resources.resource_id"), primary_key=True
    )
    licence_id = sa.Column(sa.String, primary_key=True)
    revision = sa.Column(sa.Integer, primary_key=True)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["licence_id", "revision"],
            ["licences.licence_id", "licences.revision"],
        ),
    )


class Resource(BaseModel):
    """Resource ORM model."""

    __tablename__ = "resources"

    resource_id = sa.Column(sa.VARCHAR(1024), primary_key=True)
    stac_extensions = sa.Column(sa.ARRAY(sa.VARCHAR(300)), nullable=True)
    title = sa.Column(sa.VARCHAR(1024))
    description = sa.Column(JSONB, nullable=False)
    abstract = sa.Column(sa.TEXT, nullable=False)
    contact = sa.Column(sa.ARRAY(sa.VARCHAR(300)))
    form = sa.Column(JSONB)
    citation = sa.Column(sa.TEXT)
    keywords = sa.Column(sa.ARRAY(sa.VARCHAR(300)))
    version = sa.Column(sa.VARCHAR(300))
    variables = sa.Column(JSONB)
    providers = sa.Column(JSONB)
    summaries = sa.Column(JSONB, nullable=True)
    extent = sa.Column(JSONB)
    links = sa.Column(JSONB)
    documentation = sa.Column(JSONB)
    type = sa.Column(sa.VARCHAR(300), nullable=False)
    previewimage = sa.Column(sa.TEXT)
    publication_date = sa.Column(sa.DATE)
    record_update = sa.Column(sa.types.DateTime(timezone=True), default=datetime.utcnow)
    resource_update = sa.Column(sa.DATE)

    licences = relationship(
        "Licence", secondary="resources_licences", back_populates="resources"
    )


class Licence(BaseModel):
    """Licence ORM model."""

    __tablename__ = "licences"

    licence_id = sa.Column(sa.String, primary_key=True)
    revision = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String, nullable=False)
    download_filename = sa.Column(sa.String, nullable=False)

    resources = relationship(
        "Resource", secondary="resources_licences", back_populates="licences"
    )


def init_db(connection_string: str) -> sa.engine.Engine:
    """
    Initialize the database located at URI `connection_string` and return the engine object.

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    engine = sa.create_engine(connection_string)

    # cleanup and create the schema
    metadata.drop_all(engine)
    metadata.create_all(engine)
    return engine
