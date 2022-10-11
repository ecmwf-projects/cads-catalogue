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

    # also an empty password can be set
    settings = config.SqlalchemySettings(catalogue_db_password="")
    assert settings.catalogue_db_password == ""

    # also a not empty password can be set
    temp_environ["catalogue_db_password"] = "a password"
    settings = config.SqlalchemySettings()
    assert settings.catalogue_db_password == "a password"


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
    mysettings = config.SqlalchemySettings(**my_settings_dict)
    effective_settings = config.ensure_settings(mysettings)

    assert config.dbsettings == effective_settings
    assert effective_settings == mysettings
    assert effective_settings.connection_string == my_settings_connection_string
