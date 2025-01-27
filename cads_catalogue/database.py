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
import os
from typing import Any, List

import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql as dialect_postgresql  # needed for mypy

import alembic.command
import alembic.config
from cads_catalogue import config

metadata = sa.MetaData()
BaseModel = sa.orm.declarative_base(metadata=metadata)


add_rank_function_sql = """
CREATE OR REPLACE FUNCTION ts_rank2(w real[], v1 tsvector, v2 tsvector, q tsquery, n integer) RETURNS real
LANGUAGE plpgsql
IMMUTABLE PARALLEL SAFE STRICT
AS $function$
DECLARE
    original_rank REAL;
    htp_rank REAL;
BEGIN
    SELECT INTO original_rank ts_rank(w,v1,q);
    SELECT INTO htp_rank ts_rank(v2,q);
    RETURN htp_rank*n*10 + original_rank;
END;
$function$;
"""

drop_rank_function_sql = """
DROP FUNCTION ts_rank2(w real[], v1 tsvector, v2 tsvector, q tsquery, n integer);
"""


class CatalogueUpdate(BaseModel):
    """Catalogue manager update information ORM model."""

    __tablename__ = "catalogue_updates"

    catalogue_update_id = sa.Column(sa.Integer, primary_key=True)
    update_time = sa.Column(
        sa.types.DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    catalogue_repo_commit = sa.Column(sa.String)
    metadata_repo_commit = sa.Column(dialect_postgresql.JSONB, default={})
    licence_repo_commit = sa.Column(sa.String)
    message_repo_commit = sa.Column(sa.String)
    cim_repo_commit = sa.Column(sa.String)
    content_repo_commit = sa.Column(sa.String)
    override_md = sa.Column(dialect_postgresql.JSONB, default={})
    contents_config = sa.Column(dialect_postgresql.JSONB, default={})


class Content(BaseModel):
    """Content ORM model."""

    __tablename__ = "contents"
    __table_args__ = (sa.UniqueConstraint("site", "slug", "type"),)

    content_id = sa.Column(sa.Integer, primary_key=True)
    slug = sa.Column(sa.String, index=True, nullable=False)
    content_update = sa.Column(sa.TIMESTAMP, nullable=False)
    data = sa.Column(dialect_postgresql.JSONB)
    description = sa.Column(sa.String, nullable=False)
    hidden = sa.Column(sa.Boolean, default=False, nullable=False)
    image = sa.Column(sa.String)
    layout = sa.Column(sa.String)
    link = sa.Column(sa.String)
    publication_date = sa.Column(sa.TIMESTAMP, nullable=False)
    site = sa.Column(sa.String, index=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    type = sa.Column(sa.String, index=True, nullable=False)

    keywords: sa.orm.Mapped[List["ContentKeyword"]] = sa.orm.relationship(
        "ContentKeyword", secondary="contents_keywords_m2m", back_populates="contents"
    )

    resources: sa.orm.Mapped[List["Resource"]] = sa.orm.relationship(
        "Resource",
        secondary="resources_contents",
        back_populates="contents",
        uselist=True,
    )


class ResourceContent(BaseModel):
    """many-to-many ORM model for resources-contents."""

    __tablename__ = "resources_contents"

    resource_id = sa.Column(
        sa.Integer, sa.ForeignKey("resources.resource_id"), primary_key=True
    )
    content_id = sa.Column(
        sa.Integer, sa.ForeignKey("contents.content_id"), primary_key=True
    )


class ContentKeyword(BaseModel):
    """ContentKeyword ORM model."""

    __tablename__ = "content_keywords"

    keyword_id = sa.Column(sa.Integer, primary_key=True)
    category_name = sa.Column(sa.String)
    category_value = sa.Column(sa.String)
    keyword_name = sa.Column(sa.String)

    contents: sa.orm.Mapped[List["Content"]] = sa.orm.relationship(
        "Content",
        secondary="contents_keywords_m2m",
        back_populates="keywords",
        uselist=True,
    )


class ContentsKeywordM2M(BaseModel):
    """many-to-may ORM model for contents-keywords."""

    __tablename__ = "contents_keywords_m2m"

    content_id = sa.Column(
        sa.Integer, sa.ForeignKey("contents.content_id"), primary_key=True
    )
    keyword_id = sa.Column(
        sa.Integer, sa.ForeignKey("content_keywords.keyword_id"), primary_key=True
    )


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

    resources: sa.orm.Mapped[List["Resource"]] = sa.orm.relationship(
        "Resource",
        secondary="resources_keywords",
        back_populates="keywords",
        uselist=True,
    )


class Message(BaseModel):
    """Message ORM Model."""

    __tablename__ = "messages"

    message_id = sa.Column(sa.Integer, primary_key=True)
    message_uid = sa.Column(sa.String, index=True, unique=True, nullable=False)
    date = sa.Column(sa.DateTime, nullable=False)
    site = sa.Column(sa.String, index=True)
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

    resources: sa.orm.Mapped[List["Resource"]] = sa.orm.relationship(
        "Resource",
        secondary="resources_messages",
        back_populates="messages",
        lazy="joined",
        uselist=True,
    )


class ResourceData(BaseModel):
    """Resource Data ORM model."""

    __tablename__ = "resource_data"
    __table_args__ = (
        sa.schema.UniqueConstraint("resource_uid", name="resource_uid_uc"),
    )

    resource_data_id = sa.Column(sa.Integer, primary_key=True)
    adaptor_configuration: Any = sa.Column(dialect_postgresql.JSONB)
    constraints_data: Any = sa.Column(dialect_postgresql.JSONB)
    form_data: Any = sa.Column(dialect_postgresql.JSONB)
    mapping: Any = sa.Column(dialect_postgresql.JSONB)

    resource_uid = sa.Column(
        sa.String, sa.ForeignKey("resources.resource_uid"), nullable=False
    )
    resource: sa.orm.Mapped["Resource"] = sa.orm.relationship(
        "Resource", back_populates="resource_data", uselist=False
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
    adaptor_properties_hash = sa.Column(sa.String)
    api_enforce_constraints = sa.Column(sa.Boolean, default=False)
    disabled_reason = sa.Column(sa.String)
    sources_hash = sa.Column(sa.String)
    related_resources_keywords: List[str] = sa.Column(
        dialect_postgresql.ARRAY(sa.String)
    )

    # geo extent
    geo_extent: Any = sa.Column(dialect_postgresql.JSONB)

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
    description: Any = sa.Column(dialect_postgresql.JSONB, nullable=False)
    documentation: Any = sa.Column(dialect_postgresql.JSONB)
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
    portal = sa.Column(sa.String, index=True)
    qa_flag = sa.Column(sa.Boolean)
    qos_tags = sa.Column(dialect_postgresql.ARRAY(sa.String))
    title = sa.Column(sa.String)
    topic = sa.Column(sa.String)
    type = sa.Column(sa.String, nullable=False)
    unit_measure = sa.Column(sa.String)
    use_limitation = sa.Column(sa.String)
    variables: Any = sa.Column(dialect_postgresql.JSONB)

    # fulltextsearch-related
    fulltext = sa.Column(sa.String)
    high_priority_terms = sa.Column(sa.String)
    popularity = sa.Column(sa.Integer, default=1)
    search_field: str = sa.Column(
        sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
        sa.Computed(
            "setweight(to_tsvector('english', resource_uid || ' ' || coalesce(title, '')), 'A')  || ' ' || "
            "setweight(to_tsvector('english', coalesce(abstract, '')), 'B')  || ' ' || "
            "setweight(to_tsvector('english', coalesce(fulltext, '')), 'C')  || ' ' || "
            "setweight(to_tsvector('english', coalesce(high_priority_terms, '')), 'D')",
            persisted=True,
        ),
    )
    fts: str = sa.Column(
        sqlalchemy_utils.types.ts_vector.TSVectorType(regconfig="english"),
        sa.Computed(
            "to_tsvector('english', coalesce(high_priority_terms, ''))",
            persisted=True,
        ),
    )
    # relationship attributes
    resource_data = sa.orm.relationship(
        ResourceData, uselist=False, back_populates="resource", lazy="select"
    )

    licences: sa.orm.Mapped[List["Licence"]] = sa.orm.relationship(
        "Licence",
        secondary="resources_licences",
        back_populates="resources",
        uselist=True,
    )
    messages: sa.orm.Mapped[List["Message"]] = sa.orm.relationship(
        "Message",
        secondary="resources_messages",
        back_populates="resources",
        uselist=True,
    )
    related_resources: sa.orm.Mapped[List["Resource"]] = sa.orm.relationship(
        "Resource",
        secondary=related_resources,
        primaryjoin=resource_id == related_resources.c.child_resource_id,
        secondaryjoin=resource_id == related_resources.c.parent_resource_id,
        backref=sa.orm.backref("back_related_resources"),
        uselist=True,
    )
    keywords: sa.orm.Mapped[List["Keyword"]] = sa.orm.relationship(
        "Keyword", secondary="resources_keywords", back_populates="resources"
    )

    contents: sa.orm.Mapped[List["Content"]] = sa.orm.relationship(
        "Content",
        secondary="resources_contents",
        back_populates="resources",
        uselist=True,
    )

    __table_args__ = (
        sa.Index("idx_resources_search_field", search_field, postgresql_using="gin"),
        sa.Index("idx_resources_fts", fts, postgresql_using="gin"),
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
    portal = sa.Column(sa.String)
    scope = sa.Column(
        sa.Enum("portal", "dataset", name="licence_scope"), default="dataset"
    )

    resources: sa.orm.Mapped[List["Resource"]] = sa.orm.relationship(
        "Resource",
        secondary="resources_licences",
        back_populates="licences",
        uselist=True,
    )

    __table_args__ = (
        sa.schema.UniqueConstraint(
            "licence_uid", "revision", name="licence_uid_revision_uc"
        ),
    )


def ensure_engine(connection_string, **kwargs) -> sa.engine.Engine:
    """Return a sqlalchemy engine."""
    settings = config.ensure_settings(config.dbsettings)
    engine_kwargs = {
        "pool_recycle": settings.pool_recycle,
        "pool_size": settings.pool_size,
        "pool_timeout": settings.pool_timeout,
        "max_overflow": settings.max_overflow,
    }
    engine_kwargs.update(kwargs)
    if engine_kwargs["pool_size"] == -1:
        engine = sa.create_engine(connection_string, poolclass=sa.pool.NullPool)
    else:
        engine = sa.create_engine(connection_string, **engine_kwargs)
    return engine


def ensure_session_obj(read_only: bool = False, **kwargs) -> sa.orm.sessionmaker:
    """Create a new session object bound to the catalogue database.

    Parameters
    ----------
    read_only: if True, return the sessionmaker object for read-only sessions (default False).

    Returns
    -------
    session_obj:
        a SQLAlchemy Session object
    """
    settings = config.ensure_settings(config.dbsettings)
    if read_only:
        connection_string = settings.connection_string_read
    else:
        connection_string = settings.connection_string
    engine = ensure_engine(connection_string, **kwargs)
    session_obj = sa.orm.sessionmaker(engine)
    return session_obj


def create_catalogue_functions(engine):
    """Add customized functions in the catalogue database."""
    with engine.connect() as conn:
        conn.execute(sa.text(add_rank_function_sql))
        conn.commit()


def init_database(connection_string: str, force: bool = False) -> sa.engine.Engine:
    """Make sure the db located at URI `connection_string` exists updated and return the engine object.

    :param connection_string: something like 'postgresql://user:password@netloc:port/dbname'
    :param force: if True, drop the database structure and build again from scratch

    Returns
    -------
    Engine:
        the sqlalchemy engine object
    """
    engine = sa.create_engine(connection_string)
    migration_directory = os.path.abspath(os.path.join(__file__, "..", ".."))
    os.chdir(migration_directory)
    alembic_config_path = os.path.join(migration_directory, "alembic.ini")
    alembic_cfg = alembic.config.Config(alembic_config_path)
    for option in ["drivername", "username", "password", "host", "port", "database"]:
        value = getattr(engine.url, option)
        if value is None:
            value = ""
        alembic_cfg.set_main_option(option, str(value))
    if not sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.create_database(engine.url)
        # cleanup and create the schema
        BaseModel.metadata.drop_all(engine)
        BaseModel.metadata.create_all(engine)
        create_catalogue_functions(engine)
        alembic.command.stamp(alembic_cfg, "head")
    else:
        # check the structure is empty or incomplete
        query = sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )
        with engine.connect() as conn:
            if "licences" not in conn.execute(query).scalars().all():
                force = True
    if force:
        # cleanup and create the schema
        # NOTE: tables no more in metadata are not removed with drop_all
        BaseModel.metadata.drop_all(engine)
        BaseModel.metadata.create_all(engine)
        create_catalogue_functions(engine)
        alembic.command.stamp(alembic_cfg, "head")
    else:
        # update db structure
        alembic.command.upgrade(alembic_cfg, "head")
    return engine
