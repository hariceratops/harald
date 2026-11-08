import shutil
from pathlib import Path

import pytest

from tests.docs.checker import Example, collect, parse_page, run_example
from tests.docs.sample import ROOT, build_sample_home

PARSED = collect(ROOT)


@pytest.fixture(scope="session")
def sample_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    home = tmp_path_factory.mktemp("docs-sample") / "home"
    built = build_sample_home(home)
    assert built.is_ok, str(built.unwrap_err())
    return home


@pytest.fixture
def home(sample_home: Path, tmp_path: Path) -> Path:
    return shutil.copytree(sample_home, tmp_path / "home", symlinks=True)


def _only_example(page: str) -> Example:
    (example,) = parse_page("page.md", page).examples
    return example


def _problems(page: str) -> list[str]:
    return parse_page("page.md", page).problems


@pytest.mark.parametrize(
    "example", PARSED.examples, ids=[f"{e.page}:{e.line}" for e in PARSED.examples]
)
def test_docs_example(example: Example, home: Path) -> None:
    failure = run_example(example, home)
    if failure.is_some:
        pytest.fail(failure.unwrap(), pytrace=False)


def test_docs_pages_are_well_formed() -> None:
    assert PARSED.problems == []


def test_lookup_page_is_a_checked_page() -> None:
    assert any(e.page == "docs/user/lookup.md" for e in PARSED.examples)


def test_wrong_block_fails_naming_page_line_and_diff(home: Path) -> None:
    example = _only_example("```console\n$ harald-cli lookup --en use\nnope\n```\n")
    failure = run_example(example, home)
    assert failure.is_some
    text = failure.unwrap()
    assert text.startswith("page.md:2: `harald-cli lookup --en use` printed something else")
    assert "-nope" in text
    assert "+use (verb)" in text


def test_right_block_passes_ignoring_trailing_whitespace(home: Path) -> None:
    example = _only_example(
        "```console\n$ harald-cli lookup --en use\n"
        "use (verb)   \n  employ, apply\n    benutzen\n    verwenden\n"
        "  to exhaust the supply of, to consume\n    verbrauchen\n"
        "  to exploit\n    ausnutzen\n    zum Vorwand nehmen  (use as a pretext)\n"
        "use (noun)\n  act of using\n    die Benutzung\n    der Gebrauch\n"
        "  die Anwendung\n```\n"
    )
    assert run_example(example, home).is_none


def test_the_scratch_home_prints_as_tilde(home: Path) -> None:
    example = _only_example(
        "```console\n$ harald-cli build\n"
        "unchanged: ~/.local/share/harald/lexicon.db left untouched\n"
        "Lexicon schema 7\nSources\n  Tatoeba\n    unknown   CC BY 2.0 FR\n"
        "    Tatoeba contributors (tatoeba.org)\n  Wiktionary (de)\n"
        "    2026-11-01   CC BY-SA 4.0\n"
        "    Wiktionary contributors, extracted by wiktextract (kaikki.org)\n"
        "  Wiktionary (en)\n    2026-11-01   CC BY-SA 4.0\n"
        "    Wiktionary contributors, extracted by wiktextract (kaikki.org)\n"
        "Coverage (informational)\n  verbs with complete Stammformen\n"
        "    100.0 % (1/1)\n  nouns with a gender\n    0.0 % (0/0)\n"
        "  senses with a translated example\n    0.0 % (0/1)\n```\n"
    )
    assert run_example(example, home).is_none


def test_a_failed_command_ends_the_example(home: Path) -> None:
    example = _only_example(
        "```console\n$ harald-cli lookup zzzz\nwrong\n$ harald-cli info\nwrong\n```\n"
    )
    failure = run_example(example, home).unwrap()
    assert "page.md:2:" in failure
    assert "page.md:4:" not in failure


@pytest.mark.parametrize("info", ["sh", "toml", "text"])
def test_fences_without_harald_cli_are_ignored(info: str) -> None:
    parsed = parse_page("page.md", f"```{info}\nuv sync\nkey = 1\n```\n")
    assert parsed.problems == []
    assert parsed.examples == []


@pytest.mark.parametrize(
    "page",
    [
        "```sh\nharald-cli build\n```\n",
        "```sh\nuv run harald-cli build\n```\n",
        "```sh\n$ harald-cli build\n```\n",
        "    harald-cli build\n",
        "Text\n\n$ harald-cli build\n",
        "<!-- docs: illustration x -->\n```sh\nharald-cli build\n```\n",
        "<!-- docs: nonsense -->\n```sh\nuv sync\n```\n",
        "<!-- docs: keys -->\n| Key | Does |\n|---|---|\n| `q` | quit |\n",
        "<!-- docs: keys nowhere -->\n| Key | Does |\n|---|---|\n| `q` | quit |\n",
        "<!-- docs: illustration -->\n```console\n$ harald-cli info\n```\n",
        "<!-- docs: keys home -->\n```sh\nuv sync\n```\n",
        "```console\nloose output\n$ harald-cli info\n```\n",
        "```console\n```\n",
        "```console\n$ ls\n```\n",
        "```console\n$ harald lookup lief\n```\n",
        "```console\n$ uv run harald-cli info\n```\n",
        "```console\n$ HARALD_CONFIG=x harald-cli info\n```\n",
        "```console\n$ harald-cli info | cat\n```\n",
        "```console\n$ harald-cli info > out\n```\n",
        "```console\n$ harald-cli lookup 'it\n```\n",
        "```console\n$ harald-cli prune\n```\n",
        "| Key | Does |\n|---|---|\n| `q` | quit |\n",
        "<!-- docs: keys home -->\n| Key | Does |\n|---|---|\n| quit | quit |\n",
    ],
)
def test_malformed_pages_are_problems(page: str) -> None:
    assert _problems(page) != []


@pytest.mark.parametrize(
    "page",
    [
        "<!-- docs: illustration -->\n```sh\nharald-cli build --fetch\n```\n",
        "Run `harald-cli lookup lief` to look a word up.\n",
        "<!-- an ordinary comment -->\n```sh\nuv sync\n```\n",
        "```console\n$ harald-cli prune --yes\n```\n",
        "```console\n$ harald-cli lookup lief  # a comment\n```\n",
        "<!-- docs: keys home -->\n| Key | Does |\n|---|---|\n| `q` | quit |\n",
        "- item\n\n  ```console\n  $ harald-cli info\n  ```\n",
    ],
)
def test_wellformed_pages_have_no_problems(page: str) -> None:
    assert _problems(page) == []


def test_keys_comment_parses_into_a_key_table() -> None:
    parsed = parse_page(
        "page.md",
        "<!-- docs: keys home -->\n| Key | Does |\n|---|---|\n| `l` | lookup |\n"
        "| `n` / `b` | next / back |\n",
    )
    (table,) = parsed.tables
    assert (table.page, table.line, table.screen) == ("page.md", 2, "home")
    assert [r.keys for r in table.rows] == [("l",), ("n", "b")]
    assert [r.line for r in table.rows] == [4, 5]


def test_readme_is_collected(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n")
    (tmp_path / "README.md").write_text("```sh\nharald-cli info\n```\n")
    problems = collect(tmp_path).problems
    assert [p.split(":")[0] for p in problems] == ["README.md"]
