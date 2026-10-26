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
    sub.add_parser("build", help="build lexicon.db from the locally kept sources")
    lookup = sub.add_parser("lookup", help="look up a German word")
    lookup.add_argument("--conj", action="store_true", help="show every tense")
    lookup.add_argument("words", nargs="+", metavar="WORD")
    return parser


def _build(config: Config) -> int:
    from harald.build.run import build

    res = build(config)
    if res.is_err:
        return _fail(res.unwrap_err())
    report = res.unwrap()
    print(f"{report.entries} entries, {report.bad_lines} bad lines")
    print(f"{config.lexicon} ({report.size_bytes / 1_000_000:.1f} MB) in {report.seconds:.1f} s")
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
            return _build(config)
        return _lookup(config, args.words, args.conj)
    except KeyboardInterrupt:
        return _EXIT_INTERRUPTED
