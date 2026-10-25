from collections.abc import Sequence
from pathlib import Path

import click

from harald.config import ConfigError, load_config
from harald.lexicon.errors import LexiconError

_EXIT_REFUSED = 2


@click.command(help="open the terminal UI")
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    envvar="HARALD_CONFIG",
    help="path to config.toml",
)
def tui(config_path: Path | None) -> int:
    from harald.use_cases.lexicon import QueryLexiconInfo

    loaded = load_config(config_path)
    if loaded.is_err:
        return _refuse(loaded.unwrap_err())
    config = loaded.unwrap()
    # refuse before Textual is imported, so a startup error is never drawn inside the UI
    checked = QueryLexiconInfo(config).execute()
    if checked.is_err:
        return _refuse(checked.unwrap_err())
    from harald.tui.app import HaraldApp

    HaraldApp(config).run()
    return 0


def _refuse(err: ConfigError | LexiconError) -> int:
    click.echo(err, err=True)
    return _EXIT_REFUSED


def main(argv: Sequence[str] | None = None) -> int:
    try:
        code: int = tui.main(args=argv, prog_name="harald", standalone_mode=False)
        return code
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except click.Abort:
        return 130
