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
        assert any("1 x Article" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        assert _cards(built) == []

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, EntryScreen)
        assert [t for t, _ in _cards(built)] == ["meaning_de_en", "meaning_en_de", "article"]

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
        assert len(_cards(built)) == 3

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
            "article",
            "meaning_de_de",
            "meaning_de_en",
            "meaning_en_de",
        ]

    _drive(built, (100, 30), script)


@pytest.mark.parametrize("size", SIZES)
def test_picker_steps_hint_at_space_and_an_empty_confirm_says_why(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a")
        await pilot.pause()
        step = static_lines(app.screen, "#step")
        assert any("space ticks a row" in line for line in step)
        assert all(len(line) <= size[0] for line in step)
        assert_inside(app.screen, size)
        await pilot.press("n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert any("Nothing was ticked" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        assert not any("space ticks a row" in line for line in static_lines(app.screen, "#step"))
        assert _cards(built) == []

    _drive(built, size, script)


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


@pytest.mark.parametrize("size", SIZES)
def test_a_noun_without_gender_shows_the_refusal_and_still_creates_the_rest(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Fernweh")
        await pilot.press("a", "space", "n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert any("Article - missing: gender" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        await pilot.press("c")
        await pilot.pause()
        assert [t for t, _ in _cards(built)] == ["meaning_de_de"]

    _drive(built, size, script)


def test_escape_cancels_without_writing(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "space", "n", "escape")
        await pilot.pause()
        assert isinstance(app.screen, EntryScreen)
        assert not built.config.learning_db.exists() or _cards(built) == []

    _drive(built, (40, 30), script)


def _conjugation_slots(ws: Workspace) -> list[str]:
    with sqlite3.connect(ws.config.learning_db) as db:
        rows = db.execute(
            "SELECT content ->> '$.slot' FROM card WHERE card_type = 'conjugation' ORDER BY id"
        ).fetchall()
    return [slot for (slot,) in rows]


@pytest.mark.parametrize("size", SIZES)
def test_a_verb_gets_a_tense_step_and_conjugation_cards(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "anrufen")
        await pilot.press("a", "n")
        await pilot.pause()
        assert "Step 2 of 3: Conjugation tenses" in " ".join(static_lines(app.screen, "#step"))
        picker = app.screen.query_one(SelectionList)
        assert picker.option_count == 14
        assert not picker.selected
        assert_inside(app.screen, size)
        await pilot.press("space", "n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert any("6 x Conjugation" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        assert _cards(built) == []

        await pilot.press("c")
        await pilot.pause()
        assert _conjugation_slots(built) == [
            f"ind.pres.{p}" for p in ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")
        ]

    _drive(built, size, script)


def test_tenses_that_already_have_cards_are_marked_and_need_no_sense(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "anrufen")
        await pilot.press("a", "n", "space", "n", "c")
        await pilot.pause()
        await pilot.press("a", "n")
        await pilot.pause()
        picker = app.screen.query_one(SelectionList)
        assert "(has cards)" in str(picker.get_option_at_index(0).prompt)
        assert all(
            "(has cards)" not in str(picker.get_option_at_index(i).prompt) for i in range(1, 14)
        )
        await pilot.press("space", "n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert any("nothing new" in line for line in lines)
        assert any("Already have: 6" in line for line in lines)
        await pilot.press("b", "down", "space", "n")
        await pilot.pause()
        assert any("6 x Conjugation" in line for line in static_lines(app.screen, "#summary"))
        await pilot.press("c")
        await pilot.pause()
        assert len(_conjugation_slots(built)) == 12
        assert [t for t, _ in _cards(built)].count("meaning_de_en") == 0

    _drive(built, (40, 30), script)


def test_a_noun_has_no_tense_step(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a")
        await pilot.pause()
        assert any("Step 1 of 2" in line for line in static_lines(app.screen, "#step"))

    _drive(built, (40, 12), script)
