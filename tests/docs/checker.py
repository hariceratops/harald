"""Checks the examples in the documentation pages.

Every ```console fence in docs/**/*.md and README.md is run by the test suite
(`uv run pytest tests/docs`) against a small sample lexicon. No page is exempt.

Syntax
------
A fence whose info string starts with `console` is a checked example:

    ```console
    $ harald-cli lookup --en use
    use (verb)
      ...
    ```

A line starting with `$ ` is a command. The lines under it, up to the next `$ `
line or the end of the block, are its expected output. Commands are written
bare (`harald-cli lookup lief`, not `uv run harald-cli ...`), split with POSIX
shell quoting, and a `#` starts a comment. There are no continuation lines, no
`NAME=value` prefixes, no pipes or redirects, and only `harald-cli` runs. A
command that would ask a question must pass `--yes`.

Command output is shown only in console blocks. A `sh` or `text` fence of
output without its `$ ` line cannot be detected, so that is a page rule.

Options
-------
An HTML comment on the line directly above a block carries options. The
vocabulary is closed; a new word is an edit to this module:

    <!-- docs: illustration -->      above a non-console fence that shows
                                     `harald-cli` on purpose; it is not run
    <!-- docs: keys SCREEN -->       above a `Key | Does` table; SCREEN is one
                                     of SCREENS

Any other `<!-- ... -->` comment is ignored. Inline code such as
`harald-cli lookup lief` in prose is never an invocation.

Invocation lint
---------------
`harald-cli` as a whitespace-separated word in a non-console fence or an
indented code block is a problem unless the fence is marked `illustration`.
So is a raw line outside every block that starts with `$ ` and holds the word,
which catches a fence markdown-it cannot see (one under an admonition).

Running
-------
Each example runs in its own copy of the sample home (tests/docs/sample.py):
default XDG paths inside a scratch directory, a scratch config and
`learning.db`, offline (a socket connect raises), the working directory in the
scratch home. Width is pinned to 80 columns by `COLUMNS` (see `docs_env`). The
only clock reads a CLI command reaches are the source dates, pinned by the
sample's sidecars to 2026-11-01, and the `time` attribute of `harald.build.run`
and `harald.build.graph`, frozen so timings print as 0.0 s.

Comparing
---------
Output must match line by line, ignoring trailing whitespace, with trailing
blank lines dropped. The scratch home prints as `~`. Nothing else is
normalised. The first mismatch ends the example, and the exit code is not
compared.
"""

import ast
import contextlib
import difflib
import inspect
import re
import shlex
import socket
import textwrap
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest import mock

from click.testing import CliRunner
from markdown_it import MarkdownIt
from markdown_it.token import Token
from textual.binding import Binding
from textual.keys import format_key
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Input, OptionList, SelectionList

import harald.build.graph
import harald.build.run
from harald.cli import cli, main
from harald.core.result import Result
from harald.tui.addword import AddWordScreen
from harald.tui.app import HaraldApp
from harald.tui.entry import EntryScreen
from harald.tui.home import HomeScreen
from harald.tui.lookup import LookupScreen
from harald.tui.study import StudyScreen
from tests.docs.sample import docs_env

SCREENS = ("home", "lookup", "entry", "add-word", "study")

PROGRAM = "harald-cli"
_OPERATORS = frozenset({"|", "||", "&&", ";", ">", ">>", "<", "&", "(", ")"})
_OPTION_COMMENT = re.compile(r"^\s*<!--\s*docs:\s*(.*?)\s*-->\s*$")
_VOCABULARY = "`illustration` or `keys SCREEN` (SCREEN is one of " + ", ".join(SCREENS) + ")"
_FROZEN_CLOCK = types.SimpleNamespace(monotonic=lambda: 0.0)


@dataclass(frozen=True, slots=True)
class Command:
    line: int
    text: str
    expected: list[str]


@dataclass(frozen=True, slots=True)
class Example:
    page: str
    line: int
    commands: list[Command]


@dataclass(frozen=True, slots=True)
class KeyRow:
    line: int
    keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KeyTable:
    page: str
    line: int
    screen: str
    rows: list[KeyRow]


@dataclass(frozen=True, slots=True)
class Parsed:
    examples: list[Example]
    tables: list[KeyTable]
    problems: list[str]


def _is_key_table(tokens: list[Token], start: int) -> bool:
    header = []
    for tok in tokens[start:]:
        if tok.type == "thead_close":
            break
        if tok.type == "inline":
            header.append(tok.content.strip())
    return header == ["Key", "Does"]


def _key_rows(tokens: list[Token], start: int) -> tuple[list[KeyRow], list[int]]:
    rows: list[KeyRow] = []
    keyless: list[int] = []
    in_body = False
    first_cell = False
    for tok in tokens[start:]:
        if tok.type == "table_close":
            break
        if tok.type == "tbody_open":
            in_body = True
        elif tok.type == "tr_open":
            first_cell = True
        elif tok.type == "inline" and in_body and first_cell:
            first_cell = False
            assert tok.map is not None and tok.children is not None
            line = tok.map[0] + 1
            keys = tuple(c.content for c in tok.children if c.type == "code_inline")
            if keys:
                rows.append(KeyRow(line, keys))
            else:
                keyless.append(line)
    return rows, keyless


def _command_problems(page: str, command: Command) -> list[str]:
    where = f"{page}:{command.line}"
    lexer = shlex.shlex(command.text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        words = list(lexer)
    except ValueError as err:
        return [f"{where}: cannot split `{command.text}`: {err}"]
    if not words or words[0] != PROGRAM:
        return [
            f"{where}: `{command.text}` is not run; only {PROGRAM} runs here, "
            f"so use an `sh` fence and write the command bare"
        ]
    if any(w in _OPERATORS for w in words):
        return [f"{where}: `{command.text}` uses a shell operator; show the effect in prose"]
    sub = next((cli.commands[w] for w in words[1:] if w in cli.commands), None)
    if sub is not None and any(p.name == "yes" for p in sub.params) and "--yes" not in words:
        return [
            f"{where}: `{command.text}` would prompt; pass `--yes` and describe the "
            f"question in prose"
        ]
    return []


def _fence_commands(page: str, fence: Token) -> tuple[list[Command], list[str]]:
    assert fence.map is not None
    first = fence.map[0] + 2
    commands: list[Command] = []
    problems: list[str] = []
    for offset, text in enumerate(fence.content.splitlines()):
        line = first + offset
        if text.startswith("$ "):
            commands.append(Command(line, text[2:].strip(), []))
        elif commands:
            commands[-1].expected.append(text)
        elif text.strip():
            problems.append(
                f"{page}:{line}: output before the first command; "
                f"start the block with `$ {PROGRAM} ...`"
            )
    if not commands:
        problems.append(
            f"{page}:{first - 1}: console block with no command; "
            f"start the block with `$ {PROGRAM} ...`"
        )
    for command in commands:
        problems += _command_problems(page, command)
    return commands, problems


def _outside_console(page: str, number: int) -> str:
    return (
        f"{page}:{number + 1}: {PROGRAM} outside a console block; make it a "
        f"console example or mark the fence `<!-- docs: illustration -->`"
    )


def parse_page(page: str, text: str) -> Parsed:
    lines = text.splitlines()
    tokens = MarkdownIt("commonmark").enable("table").parse(text)
    examples: list[Example] = []
    tables: list[KeyTable] = []
    problems: list[str] = []
    covered: set[int] = set()
    starts: dict[int, str] = {}

    for index, tok in enumerate(tokens):
        if tok.map is None:
            continue
        start, end = tok.map
        if tok.type in ("fence", "code_block"):
            covered.update(range(start, end))
        if tok.type == "fence":
            kind = "console" if (tok.info.split() or [""])[0] == "console" else "fence"
            starts[start] = kind
        elif tok.type == "table_open":
            starts[start] = "keytable" if _is_key_table(tokens, index) else "table"

    options: dict[int, list[str]] = {}
    commented: set[int] = set()
    for number, raw in enumerate(lines):
        if number in covered:
            continue
        match = _OPTION_COMMENT.match(raw)
        if match is None:
            continue
        words = match.group(1).split()
        where = f"{page}:{number + 1}"
        commented.add(number + 1)
        kind = starts.get(number + 1, "")
        if not words or words[0] not in ("illustration", "keys"):
            problems.append(f"{where}: unknown docs option `{match.group(1)}`; use {_VOCABULARY}")
        elif words[0] == "illustration" and len(words) != 1:
            problems.append(f"{where}: `illustration` takes no argument; use {_VOCABULARY}")
        elif words[0] == "keys" and (len(words) != 2 or words[1] not in SCREENS):
            problems.append(f"{where}: `keys` needs one screen; use {_VOCABULARY}")
        elif words[0] == "illustration" and kind == "console":
            problems.append(f"{where}: a console block is always run; use an `sh` fence")
        elif words[0] == "illustration" and kind != "fence":
            problems.append(f"{where}: `illustration` goes above a fence that shows {PROGRAM}")
        elif words[0] == "keys" and kind != "keytable":
            problems.append(f"{where}: `keys` goes above a `Key | Does` table")
        else:
            options[number + 1] = words

    for index, tok in enumerate(tokens):
        if tok.map is None:
            continue
        start = tok.map[0]
        where = f"{page}:{start + 1}"
        words = options.get(start, [])
        if tok.type == "fence" and starts[start] == "console":
            commands, found = _fence_commands(page, tok)
            problems += found
            examples.append(Example(page, start + 1, commands))
        elif tok.type in ("fence", "code_block"):
            marked = words[:1] == ["illustration"]
            for number in range(start, tok.map[1]):
                if PROGRAM in lines[number].split() and not marked:
                    problems.append(_outside_console(page, number))
                    break
        elif tok.type == "table_open" and starts[start] == "keytable":
            rows, keyless = _key_rows(tokens, index)
            problems += [f"{page}:{n}: write each key in backticks" for n in keyless]
            if words[:1] == ["keys"]:
                tables.append(KeyTable(page, start + 1, words[1], rows))
            elif start not in commented:
                problems.append(f"{where}: name its screen with `<!-- docs: keys SCREEN -->`")

    for number, raw in enumerate(lines):
        if number not in covered and raw.lstrip().startswith("$ ") and PROGRAM in raw.split():
            problems.append(_outside_console(page, number))
    return Parsed(examples, tables, problems)


def collect(root: Path) -> Parsed:
    pages = sorted((root / "docs").rglob("*.md")) + [root / "README.md"]
    examples: list[Example] = []
    tables: list[KeyTable] = []
    problems: list[str] = []
    for path in pages:
        parsed = parse_page(path.relative_to(root).as_posix(), path.read_text(encoding="utf-8"))
        examples += parsed.examples
        tables += parsed.tables
        problems += parsed.problems
    return Parsed(examples, tables, problems)


def _normalise(text: str, home: Path) -> list[str]:
    lines = [line.rstrip() for line in text.replace(str(home), "~").splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _no_network(*_: object, **__: object) -> None:
    raise RuntimeError("network access in a docs example")


def _run(args: list[str], home: Path) -> str:
    with (
        contextlib.chdir(home),
        mock.patch.object(socket.socket, "connect", _no_network),
        mock.patch.object(harald.build.run, "time", _FROZEN_CLOCK),
        mock.patch.object(harald.build.graph, "time", _FROZEN_CLOCK),
        CliRunner().isolation(env=docs_env(home)) as (_, _, output),
    ):
        main(args)
        text: str = output.getvalue().decode()
    return text


class ExampleFailed(Exception):
    pass


def run_example(example: Example, home: Path) -> Result[None, ExampleFailed]:
    for command in example.commands:
        args = shlex.split(command.text, comments=True)[1:]
        actual = _normalise(_run(args, home), home)
        expected = _normalise("\n".join(command.expected), home)
        if actual != expected:
            diff = difflib.unified_diff(
                expected, actual, "expected (page)", "actual", lineterm="", n=2
            )
            return Result.err(
                ExampleFailed(
                    f"{example.page}:{command.line}: `{command.text}` printed something else "
                    f"(example at line {example.line})\n" + "\n".join(diff)
                )
            )
    return Result.ok(None)


# These keys come from the widget, not the screen.
KEY_SCREENS: dict[str, tuple[type[Screen[Any]], tuple[type[Widget], ...]]] = {
    "home": (HomeScreen, (OptionList,)),
    "lookup": (LookupScreen, (Input, OptionList)),
    "entry": (EntryScreen, ()),
    "add-word": (AddWordScreen, (SelectionList,)),
    "study": (StudyScreen, (Input,)),
}


def _declared(cls: type) -> list[Binding]:
    return list(Binding.make_bindings(cls.__dict__.get("BINDINGS", [])))


def _bindings_of(cls: type) -> list[Binding]:
    return [b for base in cls.__mro__ for b in _declared(base)]


def handled_keys(screen: str) -> set[str]:
    cls, widgets = KEY_SCREENS[screen]
    owners: tuple[type, ...] = (cls, HaraldApp, *widgets)
    return {format_key(b.key) for c in owners for b in _bindings_of(c)}


def visible_keys(screen: str) -> dict[str, str]:
    """Visible bound keys of the screen and the app, mapped to their description."""
    cls, _ = KEY_SCREENS[screen]
    return {
        format_key(b.key): b.description
        for c in (cls, HaraldApp)
        for b in _bindings_of(c)
        if b.show
    }


def table_keys(table: KeyTable) -> set[str]:
    return {format_key(k) for row in table.rows for k in row.keys}


def uncomposed_widgets(screen: str) -> list[str]:
    cls, widgets = KEY_SCREENS[screen]
    tree = ast.parse(textwrap.dedent(inspect.getsource(cls.compose)))
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = node.func
            if isinstance(callee, ast.Subscript):
                callee = callee.value
            if isinstance(callee, ast.Name):
                called.add(callee.id)
    return [w.__name__ for w in widgets if w.__name__ not in called]


def key_table_problems(table: KeyTable) -> list[str]:
    cls, widgets = KEY_SCREENS[table.screen]
    problems: list[str] = []
    handled = handled_keys(table.screen)
    for row in table.rows:
        for key in row.keys:
            if format_key(key) not in handled:
                declared = ", ".join(w.__name__ for w in widgets) or "none"
                problems.append(
                    f"{table.page}:{row.line}: `{key}` is not handled by {cls.__name__} "
                    f"(or its declared widgets: {declared})"
                )
    shown = table_keys(table)
    for key, description in visible_keys(table.screen).items():
        if key not in shown:
            problems.append(
                f"{cls.__name__} binds `{key}` ({description}) visibly, but "
                f"{table.page}:{table.line} has no row for it"
            )
    return problems
