"""Custom alembic CLI with new default config path + db url by environment."""

import os
from typing import Optional, Sequence

import cads_catalogue
from alembic.config import CommandLine, Config

alembic_ini_path = os.path.abspath(os.path.join(__file__, "..", "..", "alembic.ini"))


class MyCommandLine(CommandLine):
    def main(self, argv: Optional[Sequence[str]] = None) -> None:
        options = self.parser.parse_args(argv)
        if not hasattr(options, "cmd"):
            self.parser.error("too few arguments")
        else:
            cfg = Config(
                file_=options.config,
                ini_section=options.name,
                cmd_opts=options,
            )
            url = cads_catalogue.config.ensure_settings().connection_string.replace(
                "%", "%%"
            )
            # passwords with special chars are urlencoded, but '%' must be escaped in ini files
            cfg.set_main_option("sqlalchemy.url", url)
            self.run_cmd(cfg, options)


def main() -> None:
    cli = MyCommandLine(prog="alembic-cli")
    config_in_parser = [p for p in cli.parser._actions if p.dest == "config"][0]
    config_in_parser.default = alembic_ini_path
    config_in_parser.help = f'Alternate config file; defaults to "{alembic_ini_path}"'
    cli.main()
