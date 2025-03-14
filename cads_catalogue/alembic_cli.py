"""Custom alembic CLI with new default config path + db url by environment."""

import os

from alembic.config import CommandLine, Config

alembic_ini_path = os.path.abspath(os.path.join(__file__, "..", "..", "alembic.ini"))


def get_alembic_config_args():
    config_args = {  # type: ignore
        "DB_USER": os.getenv("CATALOGUE_DB_USER", ""),
        "DB_PASS": os.getenv("CATALOGUE_DB_PASSWORD", ""),
        "DB_HOST": os.getenv("CATALOGUE_DB_HOST", ""),
        "DB_NAME": os.getenv("CATALOGUE_DB_NAME", ""),
    }
    return config_args


class MyCommandLine(CommandLine):
    def main(self, argv=None):
        options = self.parser.parse_args(argv)
        if not hasattr(options, "cmd"):
            self.parser.error("too few arguments")
        else:
            cfg = Config(
                file_=options.config,
                ini_section=options.name,
                cmd_opts=options,
                config_args=get_alembic_config_args(),
            )
            self.run_cmd(cfg, options)


def main():
    cli = MyCommandLine(prog="alembic-cli")
    config_in_parser = [p for p in cli.parser._actions if p.dest == "config"][0]
    config_in_parser.default = alembic_ini_path
    config_in_parser.help = f'Alternate config file; defaults to "{alembic_ini_path}"'
    cli.main()
