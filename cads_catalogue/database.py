"""SQLAlchemy ORM model."""

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

import datetime

import sqlalchemy as sa
import sqlalchemy_utils

from cads_catalogue import config

metadata = sa.MetaData()
BaseModel = sa.ext.declarative.declarative_base(metadata=metadata)


class CatalogueUpdate(BaseModel):
    """Catalogue manager update information ORM model."""

    __tablename__ = "catalogue_updates"

    catalogue_update_id = sa.Column(sa.Integer, primary_key=True)
    update_time = sa.Column(
        sa.types.DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    catalogue_repo_commit = sa.Column(sa.String)
    licence_repo_commit = sa.Column(sa.String)
    message_repo_commit = sa.Column(sa.String)


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

    # primary/surrogate keys
    resource_id = sa.Column(sa.Integer, primary_key=True)
    resource_uid = sa.Column(sa.String, index=True, unique=True, nullable=False)

    # file urls
    constraints = sa.Column(sa.String)
    form = sa.Column(sa.String)
    layout = sa.Column(sa.String)
    previewimage = sa.Column(sa.String)

    # internal functionality related
    adaptor = sa.Column(sa.Text)
    adaptor_configuration = sa.Column(sa.JSON)
    constraints_data = sa.Column(sa.JSON)
    form_data = sa.Column(sa.JSON)
    mapping = sa.Column(sa.JSON)

    # geo extent
    geo_extent = sa.Column(sa.JSON)

    # date/time
    begin_date = sa.Column(sa.Date)
    end_date = sa.Column(sa.Date)
    publication_date = sa.Column(sa.DATE)
    record_update = sa.Column(
        sa.types.DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    resource_update = sa.Column(sa.DATE)  # update_date of the source file

    # other metadata
    abstract = sa.Column(sa.TEXT, nullable=False)
    citation = sa.Column(sa.String)
    contactemail = sa.Column(sa.String)
    description = sa.Column(sa.JSON, nullable=False)
    documentation = sa.Column(sa.JSON)
    doi = sa.Column(sa.String)
    ds_contactemail = sa.Column(sa.String)
    ds_responsible_organisation = sa.Column(sa.String)
    ds_responsible_organisation_role = sa.Column(sa.String)
    file_format = sa.Column(sa.String)
    format_version = sa.Column(sa.String)
    hidden = sa.Column(sa.BOOLEAN, default=False)
    keywords = sa.Column(sa.dialects.postgresql.ARRAY(sa.VARCHAR(300)))
    lineage = sa.Column(sa.String)
    representative_fraction = sa.Column(sa.Float)
    responsible_organisation = sa.Column(sa.String)
    responsible_organisation_role = sa.Column(sa.String)
    responsible_organisation_website = sa.Column(sa.String)
    title = sa.Column(sa.String)
    topic = sa.Column(sa.String)
    type = sa.Column(sa.VARCHAR(300), nullable=False)
    unit_measure = sa.Column(sa.String)
    use_limitation = sa.Column(sa.String)
    variables = sa.Column(sa.JSON)

    # relationship attributes
    licences = sa.orm.relationship(
        "Licence", secondary="resources_licences", back_populates="resources"
    )
    related_resources = sa.orm.relationship(
        "Resource",
        secondary=related_resources,
        primaryjoin=resource_id == related_resources.c.child_resource_id,
        secondaryjoin=resource_id == related_resources.c.parent_resource_id,
        backref=sa.orm.backref("back_related_resources"),  # type: ignore
    )


class Licence(BaseModel):
    """Licence ORM model."""

    __tablename__ = "licences"

    licence_id = sa.Column(sa.Integer, primary_key=True)
    licence_uid = sa.Column(sa.String, index=True, nullable=False)
    revision = sa.Column(sa.Integer, index=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    download_filename = sa.Column(sa.String, nullable=False)

    resources = sa.orm.relationship(
        "Resource", secondary="resources_licences", back_populates="licences"
    )

    __table_args__ = (
        sa.schema.UniqueConstraint(
            "licence_uid", "revision", name="licence_uid_revision_uc"
        ),
    )


def ensure_session_obj(session_obj: sa.orm.sessionmaker | None) -> sa.orm.sessionmaker:
    """If `session_obj` is None, create a new session object.

    Parameters
    ----------
    session_obj: sqlalchemy Session object

    Returns
    -------
    session_obj:
        a SQLAlchemy Session object
    """
    if session_obj:
        return session_obj
    settings = config.ensure_settings(config.dbsettings)
    session_obj = sa.orm.sessionmaker(
        sa.create_engine(settings.connection_string, pool_recycle=settings.pool_recycle)
    )
    return session_obj


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
    if not sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.create_database(engine.url)
    # cleanup and create the schema
    metadata.drop_all(engine)
    metadata.create_all(engine)
    return engine
