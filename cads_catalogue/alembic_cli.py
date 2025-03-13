import os
from alembic.config import CommandLine, Config


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
                config_args={  # type: ignore
                    "DB_USER": os.getenv("CATALOGUE_DB_USER", ""),
                    "DB_PASS": os.getenv("CATALOGUE_DB_PASSWORD", ""),
                    "DB_HOST": os.getenv("CATALOGUE_DB_HOST", ""),
                    "DB_NAME": os.getenv("CATALOGUE_DB_NAME", "")
                }
            )
            import pdb; pdb.set_trace()
            self.run_cmd(cfg, options)


def main():
    MyCommandLine().main()
