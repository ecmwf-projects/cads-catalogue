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

import pydantic

dbsettings = None
storagesettings = None


class SqlalchemySettings(pydantic.BaseSettings):
    """Postgres-specific API settings.

    - ``catalogue_db_user``: postgres username.
    - ``catalogue_db_password``: postgres password.
    - ``catalogue_db_host``: hostname for the connection.
    - ``catalogue_db_name``: database name.
    """

    catalogue_db_user: str = "catalogue"
    catalogue_db_password: str | None = None
    catalogue_db_host: str = "catalogue-db"
    catalogue_db_name: str = "catalogue"
    pool_recycle: int = 60

    @pydantic.validator("catalogue_db_password")
    def password_must_be_set(cls: pydantic.BaseSettings, v: str | None) -> str | None:
        """Validate postgresql password."""
        if v is None:
            raise ValueError("catalogue_db_password must be set")
        return v

    @property
    def connection_string(self) -> str:
        """Create reader psql connection string."""
        return (
            f"postgresql://{self.catalogue_db_user}"
            f":{self.catalogue_db_password}@{self.catalogue_db_host}"
            f"/{self.catalogue_db_name}"
        )


class ObjectStorageSettings(pydantic.BaseSettings):
    """Set of settings to use the object storage with the catalogue manager.

    - ``object_storage_url``: object storage URL (internal)
    - ``storage_admin``: object storage admin username
    - ``storage_password``: object storage admin password
    - ``catalogue_bucket``: object storage bucket name to use for the catalogue metadata
    - ``document_storage_url``: object storage URL (public)
    """

    object_storage_url: str
    storage_admin: str
    storage_password: str
    catalogue_bucket: str
    document_storage_url: str

    @property
    def storage_kws(self) -> dict[str, str | bool]:
        """Return a dictionary to be used with the storage client."""
        return {
            "access_key": self.storage_admin,
            "secret_key": self.storage_password,
            "secure": False,
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
        storagesettings = ObjectStorageSettings()
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
