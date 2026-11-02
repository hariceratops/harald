import sqlite3
from dataclasses import replace

import pytest
from textual.pilot import Pilot
from textual.widget import Widget
from textual.widgets import Input, SelectionList, Static
from textual.widgets._footer import FooterKey

from harald.tui.addword import AddWordScreen, NoteScreen, PickEntryScreen
from harald.tui.app import HaraldApp
from harald.tui.entry import EntryScreen
from harald.use_cases.lexicon import LoadHeadword
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


def test_a_tense_with_no_forms_is_refused_and_not_reported_as_unticked(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        loaded = LoadHeadword(built.config).execute("anrufen", "verb").unwrap().unwrap()
        bare = replace(loaded, entries=(replace(loaded.entries[0], conjugation={}),))
        await app.push_screen(AddWordScreen(built.config, bare, 0))
        await pilot.pause()
        await pilot.press("n", "space", "n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert any("Präsens (all persons)" in line for line in lines)
        assert not any("Nothing was ticked" in line for line in lines)

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


@pytest.mark.parametrize("size", SIZES)
def test_a_noun_without_gender_shows_no_refusal_and_creates_its_card(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Fernweh")
        await pilot.press("a", "space", "n")
        await pilot.pause()
        lines = static_lines(app.screen, "#summary")
        assert not any("missing" in line for line in lines)
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


def _notes(ws: Workspace) -> list[tuple[str, str | None]]:
    with sqlite3.connect(ws.config.learning_db) as db:
        return db.execute("SELECT card_type, content ->> '$.note' FROM card ORDER BY id").fetchall()


def _prompts(app: HaraldApp) -> list[str]:
    picker = app.screen.query_one(SelectionList)
    return [str(picker.get_option_at_index(i).prompt) for i in range(picker.option_count)]


def _footer_keys(app: HaraldApp) -> list[tuple[str, str, int]]:
    return [
        (k.key_display or k.key, k.description, k.region.right)
        for k in app.screen.query(FooterKey)
        if k.display
    ]


def _note_box_fits(app: HaraldApp, size: tuple[int, int]) -> None:
    assert isinstance(app.screen, NoteScreen)
    assert_inside(app.screen, size)
    for widget in app.screen.walk_children(Widget):
        if widget.display and widget.region.area:
            assert widget.region.bottom <= size[1], f"{widget} runs past the height"
    assert app.screen.query_one("#note-hint").region.y <= 6


@pytest.mark.parametrize("size", SIZES)
def test_h_on_an_english_row_stores_a_note_ticks_the_row_and_the_cards_carry_it(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "h")
        await pilot.pause()
        _note_box_fits(app, size)
        app.screen.query_one(Input).value = "the animal"
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        picker = app.screen.query_one(SelectionList)
        assert _prompts(app)[0].endswith("  + note")
        assert "+ note" not in _prompts(app)[1]
        assert list(picker.selected) == [0]
        assert picker.highlighted == 0
        await pilot.press("n")
        await pilot.press("c")
        await pilot.pause()
        assert _notes(built) == [("meaning_de_en", "the animal"), ("meaning_en_de", "the animal")]

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_h_on_a_german_row_stores_a_note_for_the_de_de_card(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Fernweh")
        await pilot.press("a", "h")
        await pilot.pause()
        _note_box_fits(app, size)
        app.screen.query_one(Input).value = "wanderlust"
        await pilot.press("enter")
        await pilot.pause()
        assert any(p.endswith("  + note") for p in _prompts(app))
        assert len(app.screen.query_one(SelectionList).selected) == 1
        await pilot.press("n", "c")
        await pilot.pause()
        assert _notes(built) == [("meaning_de_de", "wanderlust")]

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_escape_leaves_the_row_unchanged_and_empty_enter_clears_the_note(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "h")
        await pilot.pause()
        app.screen.query_one(Input).value = "x"
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        assert not any("+ note" in p for p in _prompts(app))
        assert not app.screen.query_one(SelectionList).selected

        await pilot.press("h")
        await pilot.pause()
        app.screen.query_one(Input).value = "keep"
        await pilot.press("enter", "h")
        await pilot.pause()
        assert app.screen.query_one(Input).value == "keep"
        app.screen.query_one(Input).value = ""
        await pilot.press("enter")
        await pilot.pause()
        assert not any("+ note" in p for p in _prompts(app))
        await pilot.press("n", "c")
        await pilot.pause()
        assert _notes(built) == [("meaning_de_en", None), ("meaning_en_de", None)]

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_the_note_box_wording_and_the_word_warning_that_still_keeps_the_note(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "h")
        await pilot.pause()
        hint = app.screen.query_one("#note-hint", Static)
        assert static_lines(app.screen, "#note-hint") == ["Shown before you answer, both sides"]
        app.screen.query_one(Input).value = "not a hunde"
        await pilot.pause()
        assert static_lines(app.screen, "#note-hint") == ["Shown before you answer, both sides"]
        app.screen.query_one(Input).value = "a HUND, but small"
        await pilot.pause()
        assert static_lines(app.screen, "#note-hint") == ["Contains the word - Enter keeps it"]
        assert hint.region.width <= size[0]
        _note_box_fits(app, size)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("n", "c")
        await pilot.pause()
        assert _notes(built)[0] == ("meaning_de_en", "a HUND, but small")

    _drive(built, size, script)


def test_the_note_is_capped_at_36_characters(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "h")
        await pilot.pause()
        await pilot.press(*"x" * 40)
        assert app.screen.query_one(Input).value == "x" * 36

    _drive(built, (40, 12), script)


@pytest.mark.parametrize("size", SIZES)
def test_a_row_that_has_cards_refuses_a_note(built: Workspace, size: tuple[int, int]) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a", "space", "n", "c")
        await pilot.pause()
        await pilot.press("a", "h")
        await pilot.pause()
        assert isinstance(app.screen, AddWordScreen)
        assert any("notes come with card editing" in n.message for n in app._notifications)
        assert not any("+ note" in p for p in _prompts(app))
        await pilot.press("down", "h")
        await pilot.pause()
        assert isinstance(app.screen, NoteScreen)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_the_footer_shows_h_note_on_a_picker_step_and_fits_40_columns(
    built: Workspace, size: tuple[int, int]
) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await _open_entry(app, pilot, "Hund")
        await pilot.press("a")
        await pilot.pause()
        keys = _footer_keys(app)
        assert [(k, d) for k, d, _ in keys] == [
            ("n", "Next"),
            ("h", "Note"),
            ("b", "Back"),
            ("esc", "Cancel"),
        ]
        assert keys[-1][2] <= min(size[0], 40)
        await pilot.press("n")
        await pilot.pause()
        assert "Note" not in [d for _, d, _ in _footer_keys(app)]

    _drive(built, size, script)
