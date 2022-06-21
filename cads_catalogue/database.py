# type: ignore
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

    resource_id = sa.Column(sa.ForeignKey("resources.resource_id"), primary_key=True)
    licence_id = sa.Column(sa.ForeignKey("licences.licence_id"), primary_key=True)
    licence = relationship("Licence", back_populates="resources")
    resource = relationship("Resource", back_populates="licences")


class Resource(BaseModel):
    """Resource ORM model."""

    __tablename__ = "resources"

    resource_id = sa.Column(sa.VARCHAR(1024), primary_key=True)
    stac_extensions = sa.Column(sa.ARRAY(sa.VARCHAR(300)), nullable=True)
    title = sa.Column(sa.VARCHAR(1024))
    description = sa.Column(sa.VARCHAR(1024), nullable=False)
    contact = sa.Column(sa.ARRAY(sa.VARCHAR(300)))
    form = sa.Column(JSONB)
    keywords = sa.Column(sa.ARRAY(sa.VARCHAR(300)))
    version = sa.Column(sa.VARCHAR(300))
    # license = sa.Column(sa.VARCHAR(300), nullable=False)
    providers = sa.Column(JSONB)
    summaries = sa.Column(JSONB, nullable=True)
    extent = sa.Column(JSONB)
    links = sa.Column(JSONB)
    type = sa.Column(sa.VARCHAR(300), nullable=False)
    previewimageurl = sa.Column(sa.TEXT)
    last_modified = sa.Column(sa.types.DateTime(timezone=True), default=datetime.utcnow)

    licences = relationship("ResourceLicence", back_populates="resource")


class Licence(BaseModel):
    """Licence ORM model."""
    __tablename__ = "licences"
    __table_args__ = (sa.UniqueConstraint('title', 'revision', name='uix_table_col1_col2_col3'),)

    licence_id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String, nullable=False)
    revision = sa.Column(sa.String, nullable=False)
    text = sa.Column(sa.Text, nullable=False)
    download_filename = sa.Column(sa.String, nullable=False)

    resources = relationship("ResourceLicence", back_populates="licences")


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
