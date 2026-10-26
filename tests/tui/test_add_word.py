import sqlite3

import pytest
from textual.pilot import Pilot
from textual.widgets import Input, SelectionList

from harald.tui.addword import AddWordScreen, PickEntryScreen
from harald.tui.app import HaraldApp
from harald.tui.entry import EntryScreen
from tests.conftest import Workspace
from tests.tui.helpers import assert_inside, static_lines
from tests.tui.test_navigation import SIZES, _drive


async def _open_entry(app: HaraldApp, pilot: Pilot[None], word: str) -> None:
    await pilot.press("l")
    await pilot.pause()
    app.screen.query_one(Input).value = word
    await pilot.press("enter")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(app.screen, EntryScreen)


def _cards(ws: Workspace) -> list[tuple[str, str]]:
    with sqlite3.connect(ws.config.learning_db) as db:
        return db.execute(
            "SELECT card_type, content ->> '$.gloss' FROM card ORDER BY id"
        ).fetchall()


@pytest.mark.parametrize("size", SIZES)
def test_add_word_creates_both_meaning_cards(built: Workspace, size: tuple[int, int]) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        assert_inside(app.screen, size)
        await pilot.press("space", "n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert any("1 x German -> English" in line for line in lines)
        assert any("1 x English -> German" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        assert _cards(built) == []

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, EntryScreen)
        assert [t for t, _ in _cards(built)] == ["meaning_de_en", "meaning_en_de"]

    _drive(built, size, script)


def test_senses_that_already_have_cards_are_marked(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "space", "n", "c")
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        options = app.screen.query_one(SelectionList)
        assert "(has cards)" in str(options.get_option_at_index(0).prompt)
        assert "(has cards)" not in str(options.get_option_at_index(1).prompt)
        await pilot.press("space", "n")
        await pilot.pause()
        assert any("nothing new" in line for line in static_lines(app.screen, "#summary"))
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        assert len(_cards(built)) == 2

    _drive(built, (40, 30), script)


def test_a_headword_with_several_entries_asks_which_one(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Band")
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, PickEntryScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        # English senses, then German definitions, then the confirmation
        await pilot.press("space", "n")
        await pilot.pause()
        picker = app.screen.query_one(SelectionList)
        assert picker.display
        await pilot.press("space", "n")
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        assert sorted(t for t, _ in _cards(built)) == [
            "meaning_de_de",
            "meaning_de_en",
            "meaning_en_de",
        ]

    _drive(built, (100, 30), script)


def test_a_german_only_headword_goes_straight_to_the_german_step(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Fernweh")
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        assert any("Step 1 of 2" in line for line in static_lines(app.screen, "#step"))
        await pilot.press("space", "n", "c")
        await pilot.pause()
        assert [t for t, _ in _cards(built)] == ["meaning_de_de"]

    _drive(built, (40, 12), script)


def test_escape_cancels_without_writing(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "space", "n", "escape")
        await pilot.pause()
        assert isinstance(app.screen, EntryScreen)
        assert not built.config.learning_db.exists() or _cards(built) == []

    _drive(built, (40, 30), script)
