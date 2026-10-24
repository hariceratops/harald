from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click

from harald.config import ConfigError, load_config
from harald.core.result import Result
from harald.lexicon.db import Lexicon
from harald.lexicon.errors import LexiconError

_EXIT_FAILED = 1
_EXIT_REFUSED = 2
_EXIT_INTERRUPTED = 130


def _exit_code(err: Exception) -> int:
    match err:
        case ConfigError() | LexiconError():
            return _EXIT_REFUSED
        case _:
            return _EXIT_FAILED


def _fail(err: Exception) -> int:
    click.echo(err, err=True)
    return _exit_code(err)


def _print(renderable: Any) -> None:
    from rich.console import Console

    Console().print(renderable)


def _open_lexicon(config_path: Path | None) -> Result[Lexicon, ConfigError | LexiconError]:
    from harald.lexicon.db import open_lexicon

    loaded = load_config(config_path)
    if loaded.is_err:
        return Result.err(loaded.unwrap_err())
    opened = open_lexicon(loaded.unwrap().lexicon)
    if opened.is_err:
        return Result.err(opened.unwrap_err())
    return Result.ok(opened.unwrap())


@click.group()
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    envvar="HARALD_CONFIG",
    help="path to config.toml",
)
@click.pass_context
def cli(ctx: click.Context, config_path: Path | None) -> None:
    # the config is loaded by each command, so a broken one cannot break `--help`
    ctx.obj = config_path


@cli.command(help="build lexicon.db from the locally kept sources")
@click.option("--fetch", is_flag=True, help="download the sources first")
@click.option("--force", is_flag=True, help="rebuild even if nothing changed")
@click.pass_obj
def build(config_path: Path | None, fetch: bool, force: bool) -> int:
    from harald.render import render_info
    from harald.use_cases.build import BuildLexicon

    loaded = load_config(config_path)
    if loaded.is_err:
        return _fail(loaded.unwrap_err())
    config = loaded.unwrap()
    res = BuildLexicon(config).execute(fetch, force)
    if res.is_err:
        return _fail(res.unwrap_err())
    done = res.unwrap()
    report = done.report
    for outcome in report.fetched:
        click.echo(
            f"{outcome.filename}: {'downloaded' if outcome.downloaded else 'already current'}"
        )
    for filename in report.unknown_dates:
        click.echo(f"warning: no trusted date for {filename}; recorded as unknown", err=True)
    if report.unchanged:
        click.echo(f"unchanged: {config.lexicon} left untouched")
    else:
        if not report.published:
            click.echo("rebuilt identical bytes: published file left untouched")
        for t in report.timings:
            jobs = f" (jobs {t.job_seconds:.1f} s)" if t.job_seconds is not None else ""
            click.echo(f"  {t.node:<14}{t.seconds:7.1f} s{jobs}")
        click.echo(f"{report.entries} entries, {report.bad_lines} bad lines")
        click.echo(
            f"{config.lexicon} ({report.size_bytes / 1_000_000:.1f} MB) in {report.seconds:.1f} s"
        )
    _print(render_info(done.info))
    return 0


@cli.command(help="show sources, dates, attribution and coverage")
@click.pass_obj
def info(config_path: Path | None) -> int:
    from harald.render import render_info
    from harald.use_cases.lexicon import QueryLexiconInfo

    opened = _open_lexicon(config_path)
    if opened.is_err:
        return _fail(opened.unwrap_err())
    _print(render_info(QueryLexiconInfo(opened.unwrap()).execute()))
    return 0


@cli.command(help="look up a German word")
@click.option("--conj", is_flag=True, help="show every tense")
@click.argument("words", nargs=-1, required=True, metavar="WORD...")
@click.pass_obj
def lookup(config_path: Path | None, conj: bool, words: tuple[str, ...]) -> int:
    from harald.render import render_lookup
    from harald.use_cases.lexicon import LookUpGerman

    opened = _open_lexicon(config_path)
    if opened.is_err:
        return _fail(opened.unwrap_err())
    query = " ".join(words)
    result = LookUpGerman(opened.unwrap()).execute(query)
    if not result.shown:
        click.echo(f"No match for {query!r}", err=True)
        return _EXIT_FAILED
    _print(render_lookup(result, conj))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        code: int = cli.main(args=argv, prog_name="harald", standalone_mode=False)
        return code
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except click.Abort:  # click's form of KeyboardInterrupt
        return _EXIT_INTERRUPTED
