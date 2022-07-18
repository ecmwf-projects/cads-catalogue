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
dbsettings = None


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
    doi = sa.Column(sa.String)
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
    record_update = sa.Column(
        sa.types.DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    references = sa.Column(sa.JSON)
    resource_update = sa.Column(sa.DATE)
    use_eqc = sa.Column(sa.Boolean)

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


def ensure_settings(
    settings: config.SqlalchemySettings | None = None,
) -> config.SqlalchemySettings:
    """
    If `settings` is None, create a new SqlalchemySettings object.

    :param settings: an optional config.SqlalchemySettings to be set
    """
    global dbsettings
    if settings and isinstance(settings, config.SqlalchemySettings):
        dbsettings = settings
    else:
        dbsettings = config.SqlalchemySettings()
    return dbsettings


def ensure_session_obj(session_obj: sa.orm.sessionmaker | None) -> sa.orm.sessionmaker:
    """
    If `session_obj` is None, create a new session object.

    :param session_obj: sqlalchemy Session object
    """
    if session_obj:
        return session_obj
    settings = ensure_settings(dbsettings)
    session_obj = sa.orm.sessionmaker(sa.create_engine(settings))
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
