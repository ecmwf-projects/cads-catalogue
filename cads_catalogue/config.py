"""configuration utilities."""
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

import dataclasses
import os
from typing import Optional

dbsettings = None
storagesettings = None


# NOTE of class implementations inside this module:
# - type annotation of class variables must be set (and values are properly cast)
# - class variables with 'Optional[str] = None' are checked as required


@dataclasses.dataclass
class SqlalchemySettings:
    """Postgres-specific API settings.

    - ``catalogue_db_user``: postgres username.
    - ``catalogue_db_password``: postgres password.
    - ``catalogue_db_host``: hostname for the connection.
    - ``catalogue_db_name``: database name.
    """

    catalogue_db_user: str = "catalogue"
    catalogue_db_password: Optional[str] = None
    catalogue_db_host: str = "catalogue-db"
    catalogue_db_name: str = "catalogue"
    pool_recycle: int = 60

    def __init__(self, **kwargs):
        self.match_args = kwargs
        for field in dataclasses.fields(self):
            if field.name in kwargs:
                setattr(self, field.name, kwargs[field.name])
            else:
                setattr(self, field.name, field.default)
        self.__post_init__()

    def __post_init__(self):
        # overwrite instance getting attributes from the environment
        environ = os.environ.copy()
        environ_lower = {k.lower(): v for k, v in environ.items()}
        for field in dataclasses.fields(self):
            if field.name in self.match_args:
                # do not overwrite if passed to __init__
                continue
            if field.name in environ:
                setattr(self, field.name, environ[field.name])
            elif field.name in environ_lower:
                setattr(self, field.name, environ_lower[field.name])

        # automatic casting
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if field.type is not None and not isinstance(value, field.type):
                try:
                    setattr(self, field.name, field.type(value))
                except:  # noqa
                    raise ValueError(
                        f"{field.name} '{value}' has not type {repr(field.type)}"
                    )

        # validations
        for field in dataclasses.fields(self):
            if field.default is None and getattr(self, field.name) is None:
                #  not specified field, with default None
                raise ValueError(f"{field.name} must be set")

    @property
    def connection_string(self) -> str:
        """Create reader psql connection string."""
        return (
            f"postgresql://{self.catalogue_db_user}"
            f":{self.catalogue_db_password}@{self.catalogue_db_host}"
            f"/{self.catalogue_db_name}"
        )


@dataclasses.dataclass(kw_only=True)
class ObjectStorageSettings:
    """Set of settings to use the object storage with the catalogue manager.

    - ``object_storage_url``: object storage URL (internal)
    - ``storage_admin``: object storage admin username
    - ``storage_password``: object storage admin password
    - ``catalogue_bucket``: object storage bucket name to use for the catalogue metadata
    - ``document_storage_url``: object storage URL (public)
    """

    object_storage_url: str
    storage_admin: str
    catalogue_bucket: str
    document_storage_url: str
    storage_password: Optional[str] = None

    def __init__(self, **kwargs):
        self.match_args = kwargs
        for field in dataclasses.fields(self):
            if field.name in kwargs:
                setattr(self, field.name, kwargs[field.name])
            else:
                setattr(self, field.name, field.default)
        self.__post_init__()

    def __post_init__(self):
        # overwrite instance getting attributes from the environment
        environ = os.environ.copy()
        environ_lower = {k.lower(): v for k, v in environ.items()}
        for field in dataclasses.fields(self):
            if field.name in self.match_args:
                # do not overwrite if passed to __init__
                continue
            if field.name in environ:
                setattr(self, field.name, environ[field.name])
            elif field.name in environ_lower:
                setattr(self, field.name, environ_lower[field.name])

        # automatic casting
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if field.type is not None and not isinstance(value, field.type):
                try:
                    setattr(self, field.name, field.type(value))
                except:  # noqa
                    raise ValueError(
                        f"{field.name} '{value}' has not type {repr(field.type)}"
                    )

        # validations
        # import pdb; pdb.set_trace()
        for field in dataclasses.fields(self):
            if field.default is None and getattr(self, field.name) is None:
                #  not specified field, with default None
                raise ValueError(f"{field.name} must be set")

    @property
    def storage_kws(self) -> dict[str, str | bool | None]:
        """Return a dictionary to be used with the storage client."""
        return {
            "aws_access_key_id": self.storage_admin,
            "aws_secret_access_key": self.storage_password,
        }


def ensure_storage_settings(
    settings: ObjectStorageSettings | None = None,
) -> ObjectStorageSettings:
    """If `settings` is None, create a new ObjectStorageSettings object.

    Parameters
    ----------
    settings: an optional config.ObjectStorageSettings to be set

    Returns
    -------
    ObjectStorageSettings:
        a ObjectStorageSettings object
    """
    global storagesettings
    if settings and isinstance(settings, ObjectStorageSettings):
        storagesettings = settings
    else:
        storagesettings = ObjectStorageSettings()  # type: ignore
    return storagesettings


def ensure_settings(settings: SqlalchemySettings | None = None) -> SqlalchemySettings:
    """If `settings` is None, create a new SqlalchemySettings object.

    Parameters
    ----------
    settings: an optional config.SqlalchemySettings to be set

    Returns
    -------
    sqlalchemysettings:
        a SqlalchemySettings object
    """
    global dbsettings
    if settings and isinstance(settings, SqlalchemySettings):
        dbsettings = settings
    else:
        dbsettings = SqlalchemySettings()
    return dbsettings
