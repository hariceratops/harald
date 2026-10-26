import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from harald.config import Config, ConfigError, load_config
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
    print(err, file=sys.stderr)
    return _exit_code(err)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harald")
    parser.add_argument("--config", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="build lexicon.db from the locally kept sources")
    build.add_argument("--fetch", action="store_true", help="download the sources first")
    build.add_argument("--force", action="store_true", help="rebuild even if nothing changed")
    sub.add_parser("info", help="show sources, dates, attribution and coverage")
    lookup = sub.add_parser("lookup", help="look up a German word")
    lookup.add_argument("--conj", action="store_true", help="show every tense")
    lookup.add_argument("words", nargs="+", metavar="WORD")
    return parser


def _build(config: Config, fetch: bool, force: bool) -> int:
    from harald.build.run import build

    res = build(config, fetch, force)
    if res.is_err:
        return _fail(res.unwrap_err())
    report = res.unwrap()
    for outcome in report.fetched:
        print(f"{outcome.filename}: {'downloaded' if outcome.downloaded else 'already current'}")
    for filename in report.unknown_dates:
        print(f"warning: no trusted date for {filename}; recorded as unknown", file=sys.stderr)
    if report.unchanged:
        print(f"unchanged: {config.lexicon} left untouched")
        return _info(config)
    if not report.published:
        print("rebuilt identical bytes: published file left untouched")
    for t in report.timings:
        jobs = f" (jobs {t.job_seconds:.1f} s)" if t.job_seconds is not None else ""
        print(f"  {t.node:<14}{t.seconds:7.1f} s{jobs}")
    print(f"{report.entries} entries, {report.bad_lines} bad lines")
    print(f"{config.lexicon} ({report.size_bytes / 1_000_000:.1f} MB) in {report.seconds:.1f} s")
    return _info(config)


def _info(config: Config) -> int:
    from rich.console import Console

    from harald.lexicon.db import open_lexicon
    from harald.lexicon.info import load_info
    from harald.lexicon.schema import SCHEMA_VERSION
    from harald.render import render_info

    opened = open_lexicon(config.lexicon)
    if opened.is_err:
        return _fail(opened.unwrap_err())
    Console().print(render_info(load_info(opened.unwrap(), SCHEMA_VERSION)))
    return 0


def _lookup(config: Config, words: list[str], full_conjugation: bool) -> int:
    from rich.console import Console

    from harald.lexicon.db import open_lexicon
    from harald.lexicon.lookup import lookup_de
    from harald.render import render_lookup

    opened = open_lexicon(config.lexicon)
    if opened.is_err:
        return _fail(opened.unwrap_err())
    query = " ".join(words)
    result = lookup_de(opened.unwrap(), query)
    if not result.shown:
        print(f"No match for {query!r}", file=sys.stderr)
        return _EXIT_FAILED
    Console().print(render_lookup(result, full_conjugation))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config_path = args.config or (Path(p) if (p := os.environ.get("HARALD_CONFIG")) else None)
    try:
        loaded = load_config(config_path)
        if loaded.is_err:
            return _fail(loaded.unwrap_err())
        config = loaded.unwrap()
        if args.command == "build":
            return _build(config, args.fetch, args.force)
        if args.command == "info":
            return _info(config)
        return _lookup(config, args.words, args.conj)
    except KeyboardInterrupt:
        return _EXIT_INTERRUPTED
