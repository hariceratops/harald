import pytest

from tests.docs.checker import (
    KEY_SCREENS,
    SCREENS,
    KeyTable,
    collect,
    key_table_problems,
    parse_page,
    uncomposed_widgets,
)
from tests.docs.sample import ROOT

TABLES = collect(ROOT).tables


def _table(page: str) -> KeyTable:
    (table,) = parse_page("page.md", page).tables
    return table


@pytest.mark.parametrize("table", TABLES, ids=[f"{t.page}:{t.line}" for t in TABLES])
def test_key_table(table: KeyTable) -> None:
    assert key_table_problems(table) == []


def test_each_screen_has_one_key_table() -> None:
    named = sorted(t.screen for t in TABLES)
    assert named == sorted(SCREENS)


def test_screens_vocabulary_matches_key_screens() -> None:
    assert set(SCREENS) == set(KEY_SCREENS)


@pytest.mark.parametrize("screen", SCREENS)
def test_declared_widgets_are_composed(screen: str) -> None:
    assert uncomposed_widgets(screen) == []


def test_unhandled_key_fails_naming_the_row() -> None:
    table = _table(
        "<!-- docs: keys entry -->\n| Key | Does |\n|---|---|\n"
        "| `c` | a |\n| `a` | b |\n| `esc` | c |\n| `x` | d |\n"
    )
    (problem,) = key_table_problems(table)
    assert problem.startswith("page.md:7: `x` is not handled by EntryScreen")


def test_missing_visible_binding_fails() -> None:
    table = _table(
        "<!-- docs: keys entry -->\n| Key | Does |\n|---|---|\n| `c` | a |\n| `esc` | c |\n"
    )
    (problem,) = key_table_problems(table)
    assert "EntryScreen binds `a`" in problem


def test_widget_key_passes_only_when_the_widget_is_declared() -> None:
    head = "<!-- docs: keys entry -->\n| Key | Does |\n|---|---|\n"
    keys = "| `c` | a |\n| `a` | b |\n| `esc` | c |\n"
    assert key_table_problems(_table(head + keys + "| `enter` | x |\n")) != []
    lookup = "<!-- docs: keys lookup -->\n| Key | Does |\n|---|---|\n| `enter` | x |\n"
    assert not any("`enter`" in p for p in key_table_problems(_table(lookup)))


def test_aliases_match_through_textual_names() -> None:
    table = _table(
        "<!-- docs: keys lookup -->\n| Key | Does |\n|---|---|\n| `esc` | a |\n| `/` | b |\n"
    )
    assert key_table_problems(table) == []
