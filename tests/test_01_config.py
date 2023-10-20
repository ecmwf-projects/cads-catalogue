from typing import Any

import pytest
import sqlalchemy as sa

from cads_catalogue import config


def test_sqlalchemysettings(temp_environ: Any) -> None:
    # check settings must have a password set (no default)
    temp_environ.update(
        dict(
            catalogue_db_host="host1",
            catalogue_db_host_read="host2",
            catalogue_db_name="dbname",
            catalogue_db_user="dbuser",
        )
    )
    temp_environ.pop("catalogue_db_password", default=None)
    with pytest.raises(ValueError):
        config.SqlalchemySettings()

    # also an empty password can be set
    settings = config.SqlalchemySettings(
        catalogue_db_password="",
        catalogue_db_host="host1",
        catalogue_db_host_read="host2",
        catalogue_db_name="dbname1",
        catalogue_db_user="user1",
    )
    assert settings.catalogue_db_password == ""
    config.dbsettings = None

    # also a not empty password can be set
    temp_environ.update(
        dict(
            catalogue_db_password="apassword",
            catalogue_db_host="host1",
            catalogue_db_host_read="host2",
            catalogue_db_name="dbname",
            catalogue_db_user="dbuser",
        )
    )
    settings = config.SqlalchemySettings()
    assert settings.catalogue_db_password == "apassword"
    config.dbsettings = None
    assert settings.connection_string == "postgresql://dbuser:apassword@host1/dbname"
    assert (
        settings.connection_string_read == "postgresql://dbuser:apassword@host2/dbname"
    )


def test_ensure_settings(session_obj: sa.orm.sessionmaker, temp_environ: Any) -> None:
    temp_environ["catalogue_db_user"] = "auser"
    temp_environ["catalogue_db_password"] = "apassword"
    temp_environ["catalogue_db_host"] = "ahost"
    temp_environ["catalogue_db_host_read"] = "ahost2"
    temp_environ["catalogue_db_name"] = "aname"
    # initially global settings is importable, but it is None
    assert config.dbsettings is None

    # at first run returns right connection and set global setting
    effective_settings = config.ensure_settings()
    assert (
        effective_settings.connection_string
        == "postgresql://auser:apassword@ahost/aname"
    )
    assert (
        effective_settings.connection_string_read
        == "postgresql://auser:apassword@ahost2/aname"
    )
    assert config.dbsettings == effective_settings
    config.dbsettings = None

    # setting a custom configuration works as well
    my_settings_dict = {
        "catalogue_db_user": "monica",
        "catalogue_db_password": "secret1",
        "catalogue_db_host": "myhost",
        "catalogue_db_host_read": "myhost2",
        "catalogue_db_name": "mybroker",
    }
    my_settings_connection_string = (
        "postgresql://%(catalogue_db_user)s:%(catalogue_db_password)s"
        "@%(catalogue_db_host)s/%(catalogue_db_name)s" % my_settings_dict
    )
    my_settings_connection_string_ro = (
        "postgresql://%(catalogue_db_user)s:%(catalogue_db_password)s"
        "@%(catalogue_db_host_read)s/%(catalogue_db_name)s" % my_settings_dict
    )
    mysettings = config.SqlalchemySettings(**my_settings_dict)
    effective_settings = config.ensure_settings(mysettings)

    assert config.dbsettings == effective_settings
    assert effective_settings == mysettings
    assert effective_settings.connection_string == my_settings_connection_string
    assert effective_settings.connection_string_read == my_settings_connection_string_ro
    config.dbsettings = None


def test_storagesettings(temp_environ: Any) -> None:
    # check settings must have a password set (no default)
    temp_environ.pop("storage_password", default=None)
    with pytest.raises(ValueError) as excinfo:
        config.ObjectStorageSettings()  # type: ignore
    assert "must be set" in str(excinfo.value)
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
        "aws_access_key_id": "admin1",
        "aws_secret_access_key": "secret1",
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
        "aws_access_key_id": "admin1",
        "aws_secret_access_key": "secret1",
    }
    mysettings = config.ObjectStorageSettings(**my_settings_dict)
    effective_settings = config.ensure_storage_settings(mysettings)

    assert config.storagesettings == effective_settings
    assert effective_settings == mysettings
    assert effective_settings.storage_kws == my_settings_storage_kws
    config.dbsettings = None
