"""SQLAlchemy ORM model"""
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

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


def init_database(connection_string: str) -> sa.engine.Engine:
    """
    Initialize the database located at URI `connection_string` and return the engine object.

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    """
    engine = sa.create_engine(connection_string)

    # cleanup and create the schema
    metadata.drop_all(engine)
    metadata.create_all(engine)
    return engine
