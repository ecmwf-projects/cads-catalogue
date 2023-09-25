from typing import Any

import pytest
import sqlalchemy as sa

from cads_catalogue import config


def test_sqlalchemysettings(temp_environ: Any) -> None:
    # check settings must have a password set (no default)
    temp_environ.pop("catalogue_db_password", default=None)
    with pytest.raises(ValueError) as excinfo:
        config.SqlalchemySettings()
    assert "read_db_user" in str(excinfo.value)

    # also an empty password can be set
    temp_environ["catalogue_db_user"] = "user1"
    temp_environ["catalogue_db_host"] = "host1"
    temp_environ["catalogue_db_name"] = "dbname1"
    settings = config.SqlalchemySettings(catalogue_db_password="")
    assert settings.catalogue_db_password == ""

    # check backward compatibility defaults
    assert settings.__dict__ == {
        "catalogue_db_user": "user1",
        "catalogue_db_password": "",
        "catalogue_db_host": "host1",
        "catalogue_db_name": "dbname1",
        "read_db_user": "user1",
        "read_db_password": "",
        "write_db_user": "user1",
        "write_db_password": "",
        "db_host": "host1",
        "pool_recycle": 60,
        "match_args": {"catalogue_db_password": ""},
    }

    # use not backward compatibility variables
    temp_environ["read_db_user"] = "ro_user"
    temp_environ["read_db_password"] = "ro_password"
    temp_environ["write_db_user"] = "rw_user"
    temp_environ["write_db_password"] = "rw_password"
    temp_environ["db_host"] = "new_db_host"
    settings = config.SqlalchemySettings()
    assert settings.__dict__ == {
        "catalogue_db_user": "user1",
        "catalogue_db_password": None,
        "catalogue_db_host": "host1",
        "catalogue_db_name": "dbname1",
        "read_db_user": "ro_user",
        "read_db_password": "ro_password",
        "write_db_user": "rw_user",
        "write_db_password": "rw_password",
        "db_host": "new_db_host",
        "pool_recycle": 60,
        "match_args": {},
    }
    assert (
        settings.connection_string
        == "postgresql://rw_user:rw_password@new_db_host/dbname1"
    )
    assert (
        settings.connection_string_ro
        == "postgresql://ro_user:ro_password@new_db_host/dbname1"
    )


def test_ensure_settings(session_obj: sa.orm.sessionmaker, temp_environ: Any) -> None:
    temp_environ["catalogue_db_user"] = "auser"
    temp_environ["catalogue_db_password"] = "apassword"
    temp_environ["catalogue_db_host"] = "ahost"
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
        effective_settings.connection_string_ro
        == "postgresql://auser:apassword@ahost/aname"
    )
    assert config.dbsettings == effective_settings
    config.dbsettings = None

    # setting a custom configuration works as well
    my_settings_dict = {
        "catalogue_db_user": "monica",
        "catalogue_db_password": "secret1",
        "catalogue_db_host": "myhost",
        "catalogue_db_name": "mybroker",
        "read_db_user": "ro_user",
        "read_db_password": "ro_password",
        "write_db_user": "rw_user",
        "write_db_password": "rw_password",
        "db_host": "new_db_host",
    }
    my_settings_connection_string = (
        "postgresql://%(write_db_user)s:%(write_db_password)s"
        "@%(db_host)s/%(catalogue_db_name)s" % my_settings_dict
    )
    my_settings_connection_string_ro = (
        "postgresql://%(read_db_user)s:%(read_db_password)s"
        "@%(db_host)s/%(catalogue_db_name)s" % my_settings_dict
    )
    mysettings = config.SqlalchemySettings(**my_settings_dict)
    effective_settings = config.ensure_settings(mysettings)

    assert config.dbsettings == effective_settings
    assert effective_settings == mysettings
    assert effective_settings.connection_string == my_settings_connection_string
    assert effective_settings.connection_string_ro == my_settings_connection_string_ro
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
