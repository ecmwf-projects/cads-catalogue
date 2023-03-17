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


DB_VERSION = 9  # to increment at each structure change


class DBRelease(BaseModel):
    """Information about current structure version."""

    __tablename__ = "db_release"

    db_release_version = sa.Column(sa.Integer, primary_key=True)


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


class ResourceKeyword(BaseModel):
    """many-to-may ORM model for resources-keywords."""

    __tablename__ = "resources_keywords"

    resource_id = sa.Column(
        sa.Integer, sa.ForeignKey("resources.resource_id"), primary_key=True
    )
    keyword_id = sa.Column(
        sa.Integer, sa.ForeignKey("keywords.keyword_id"), primary_key=True
    )


class ResourceMessage(BaseModel):
    """many-to-many ORM model for resources-messages."""

    __tablename__ = "resources_messages"

    resource_id = sa.Column(
        sa.Integer, sa.ForeignKey("resources.resource_id"), primary_key=True
    )
    message_id = sa.Column(
        sa.Integer, sa.ForeignKey("messages.message_id"), primary_key=True
    )


class Keyword(BaseModel):
    """Keyword ORM model."""

    __tablename__ = "keywords"

    keyword_id = sa.Column(sa.Integer, primary_key=True)
    category_name = sa.Column(sa.String)
    category_value = sa.Column(sa.String)
    keyword_name = sa.Column(sa.String)

    resources = sa.orm.relationship(
        "Resource", secondary="resources_keywords", back_populates="keywords"
    )


class Message(BaseModel):
    """Message ORM Model."""

    __tablename__ = "messages"

    message_id = sa.Column(sa.Integer, primary_key=True)
    message_uid = sa.Column(sa.String, index=True, unique=True, nullable=False)
    date = sa.Column(sa.DateTime, nullable=False)
    summary = sa.Column(sa.String, nullable=True)
    url = sa.Column(sa.String)
    severity = sa.Column(
        sa.Enum("info", "warning", "critical", "success", name="severity"),
        nullable=False,
        default="info",
    )
    content = sa.Column(sa.String)
    is_global = sa.Column(sa.Boolean)
    live = sa.Column(sa.Boolean)
    status = sa.Column(sa.Enum("ongoing", "closed", "fixed", name="msg_status"))

    resources = sa.orm.relationship(
        "Resource",
        secondary="resources_messages",
        back_populates="messages",
        lazy="joined",
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
    adaptor = sa.Column(sa.String)
    adaptor_configuration = sa.Column(sa.dialects.postgresql.JSONB)
    constraints_data = sa.Column(sa.dialects.postgresql.JSONB)
    form_data = sa.Column(sa.dialects.postgresql.JSONB)
    mapping = sa.Column(sa.dialects.postgresql.JSONB)
    related_resources_keywords = sa.Column(sa.dialects.postgresql.ARRAY(sa.String))

    # geo extent
    geo_extent = sa.Column(sa.dialects.postgresql.JSONB)

    # date/time
    begin_date = sa.Column(sa.Date)
    end_date = sa.Column(sa.Date)
    publication_date = sa.Column(sa.Date)
    record_update = sa.Column(
        sa.types.DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    resource_update = sa.Column(sa.Date)  # update_date of the source file

    # other metadata
    abstract = sa.Column(sa.String, nullable=False)
    citation = sa.Column(sa.String)
    contactemail = sa.Column(sa.String)
    description = sa.Column(sa.dialects.postgresql.JSONB, nullable=False)
    documentation = sa.Column(sa.dialects.postgresql.JSONB)
    doi = sa.Column(sa.String)
    ds_contactemail = sa.Column(sa.String)
    ds_responsible_organisation = sa.Column(sa.String)
    ds_responsible_organisation_role = sa.Column(sa.String)
    file_format = sa.Column(sa.String)
    format_version = sa.Column(sa.String)
    hidden = sa.Column(sa.Boolean, default=False)
    lineage = sa.Column(sa.String)
    representative_fraction = sa.Column(sa.Float)
    responsible_organisation = sa.Column(sa.String)
    responsible_organisation_role = sa.Column(sa.String)
    responsible_organisation_website = sa.Column(sa.String)
    title = sa.Column(sa.String)
    topic = sa.Column(sa.String)
    type = sa.Column(sa.String, nullable=False)
    unit_measure = sa.Column(sa.String)
    use_limitation = sa.Column(sa.String)
    variables = sa.Column(sa.dialects.postgresql.JSONB)

    # relationship attributes
    licences = sa.orm.relationship(
        "Licence", secondary="resources_licences", back_populates="resources"
    )
    messages = sa.orm.relationship(
        "Message", secondary="resources_messages", back_populates="resources"
    )
    related_resources = sa.orm.relationship(
        "Resource",
        secondary=related_resources,
        primaryjoin=resource_id == related_resources.c.child_resource_id,
        secondaryjoin=resource_id == related_resources.c.parent_resource_id,
        backref=sa.orm.backref("back_related_resources"),  # type: ignore
    )
    keywords = sa.orm.relationship(
        "Keyword", secondary="resources_keywords", back_populates="resources"
    )


class Licence(BaseModel):
    """Licence ORM model."""

    __tablename__ = "licences"

    licence_id = sa.Column(sa.Integer, primary_key=True)
    licence_uid = sa.Column(sa.String, index=True, nullable=False)
    revision = sa.Column(sa.Integer, index=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    download_filename = sa.Column(sa.String, nullable=False)
    md_filename = sa.Column(sa.String, nullable=False)
    scope = sa.Column(
        sa.Enum("portal", "dataset", name="licence_scope"), default="dataset"
    )

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
    session_obj = sa.orm.sessionmaker(engine)
    # add structure version
    with session_obj.begin() as session:  # type: ignore
        session.add(DBRelease(db_release_version=DB_VERSION))
    return engine
