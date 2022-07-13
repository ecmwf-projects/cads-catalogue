import pydantic


class SqlalchemySettings(pydantic.BaseSettings):
    """Postgres-specific API settings.

    - ``postgres_user``: postgres username.
    - ``postgres_password``: postgres password.
    - ``postgres_host``: hostname for the connection.
    - ``postgres_dbname``: database name.
    """

    postgres_user: str = "catalogue"
    postgres_password: str = "password"
    postgres_host: str = "catalogue-db"
    postgres_dbname: str = "catalogue"

    @property
    def connection_string(self) -> str:
        """Create reader psql connection string."""
        return (
            f"postgresql://{self.postgres_user}"
            f":{self.postgres_password}@{self.postgres_host}"
            f"/{self.postgres_dbname}"
        )
