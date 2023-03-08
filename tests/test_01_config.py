from typing import Any

import pytest
import sqlalchemy as sa

from cads_catalogue import config


def test_sqlalchemysettings(temp_environ: Any) -> None:
    # check settings must have a password set (no default)
    temp_environ.pop("catalogue_db_password", default=None)
    with pytest.raises(ValueError) as excinfo:
        config.SqlalchemySettings()
    assert "catalogue_db_password" in str(excinfo.value)
    config.dbsettings = None

    # also an empty password can be set
    settings = config.SqlalchemySettings(catalogue_db_password="")
    assert settings.catalogue_db_password == ""
    config.dbsettings = None

    # also a not empty password can be set
    temp_environ["catalogue_db_password"] = "a password"
    settings = config.SqlalchemySettings()
    assert settings.catalogue_db_password == "a password"
    config.dbsettings = None


def test_ensure_settings(session_obj: sa.orm.sessionmaker, temp_environ: Any) -> None:
    temp_environ["catalogue_db_password"] = "apassword"

    # initially global settings is importable, but it is None
    assert config.dbsettings is None

    # at first run returns right connection and set global setting
    effective_settings = config.ensure_settings()
    assert (
        effective_settings.connection_string
        == "postgresql://catalogue:apassword@catalogue-db/catalogue"
    )
    assert config.dbsettings == effective_settings
    config.dbsettings = None

    # setting a custom configuration works as well
    my_settings_dict = {
        "catalogue_db_user": "monica",
        "catalogue_db_password": "secret1",
        "catalogue_db_host": "myhost",
        "catalogue_db_name": "mycatalogue",
    }
    my_settings_connection_string = (
        "postgresql://%(catalogue_db_user)s:%(catalogue_db_password)s"
        "@%(catalogue_db_host)s/%(catalogue_db_name)s" % my_settings_dict
    )
    mysettings = config.SqlalchemySettings(**my_settings_dict)  # type: ignore
    effective_settings = config.ensure_settings(mysettings)

    assert config.dbsettings == effective_settings
    assert effective_settings == mysettings
    assert effective_settings.connection_string == my_settings_connection_string
    config.dbsettings = None


def test_storagesettings(temp_environ: Any) -> None:
    # check settings must have a password set (no default)
    temp_environ.pop("storage_password", default=None)
    with pytest.raises(ValueError) as excinfo:
        config.ObjectStorageSettings()  # type: ignore
    assert "storage_password" in str(excinfo.value)
    config.storagesettings = None

    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    for k, v in my_settings_dict.items():
        temp_environ[k] = v

    settings = config.ObjectStorageSettings()  # type: ignore
    for k, v in my_settings_dict.items():
        assert v == getattr(settings, k)
    config.storagesettings = None


def test_ensure_storage_settings(
    session_obj: sa.orm.sessionmaker, temp_environ: Any
) -> None:
    # initially global settings is importable, but it is None
    assert config.storagesettings is None

    # at first run returns right connection and set global setting
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    for k, v in my_settings_dict.items():
        temp_environ[k] = v
    effective_settings = config.ensure_storage_settings()
    assert effective_settings.storage_kws == {
        "access_key": "admin1",
        "secret_key": "secret1",
        "secure": False,
    }

    assert config.storagesettings == effective_settings
    config.storagesettings = None

    # setting a custom configuration works as well
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    my_settings_storage_kws = {
        "access_key": "admin1",
        "secret_key": "secret1",
        "secure": False,
    }
    mysettings = config.ObjectStorageSettings(**my_settings_dict)
    effective_settings = config.ensure_storage_settings(mysettings)

    assert config.storagesettings == effective_settings
    assert effective_settings == mysettings
    assert effective_settings.storage_kws == my_settings_storage_kws
    config.dbsettings = None
