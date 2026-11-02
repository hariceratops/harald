import asyncio
import json
import sqlite3
from datetime import UTC, datetime

import pytest
from textual.pilot import Pilot
from textual.widget import Widget
from textual.widgets import Button, Input

from harald.core.result import Result
from harald.learning.content import CardPlan
from harald.learning.errors import StorageError
from harald.tui.app import HaraldApp
from harald.tui.home import HomeScreen
from harald.tui.study import StudyScreen, SummaryScreen
from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LoadHeadword
from harald.use_cases.study import Grade, NextCard
from tests.conftest import Workspace
from tests.tui.helpers import assert_inside, static_lines
from tests.tui.test_navigation import SIZES, _drive


def _seed(ws: Workspace, card_types: tuple[str, ...] = ("meaning_de_en", "meaning_en_de")) -> None:
    hund = LoadHeadword(ws.config).execute("Hund", "noun").unwrap().unwrap()
    plan = PlanWordCards(ws.config).execute(hund, 0, [0], []).unwrap()
    plan = CardPlan(
        plan.word_hint, tuple(c for c in plan.cards if c.card_type in card_types), plan.refusals
    )
    CreateWordCards(ws.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()


def _reviews(ws: Workspace) -> list[tuple[int, str]]:
    with sqlite3.connect(ws.config.learning_db) as db:
        return db.execute("SELECT rating, session_id FROM review ORDER BY id").fetchall()


@pytest.mark.parametrize("size", SIZES)
def test_study_reveal_grade_and_summary(built: Workspace, size: tuple[int, int]) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, StudyScreen)
        assert any("der Hund" in line for line in static_lines(app.screen, "#card"))
        assert app.screen.query_one("#reveal", Button).display
        assert app.screen.query_one("#fields").display
        assert not app.screen.query_one("#grade2", Button).display
        assert_inside(app.screen, size)

        await pilot.press(*"dog", "enter")
        await pilot.pause()
        assert app.screen.query_one("#grade2", Button).display
        assert not app.screen.query_one("#fields").display
        assert any("you: dog" in line for line in static_lines(app.screen, "#card"))
        assert_inside(app.screen, size)
        await pilot.press("2")
        await pilot.pause()
        assert [r for r, _ in _reviews(built)] == [3]
        assert _answers(built) == [(3, "dog")]

        await pilot.press("enter")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("No answer - graded Again" in line for line in lines)
        assert any("you: (no answer)" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert app.screen.query_one("#cont", Button).display
        assert [r for r, _ in _reviews(built)] == [3, 1]
        assert _answers(built)[1] == (1, "")
        assert_inside(app.screen, size)
        # the lapsed card is inside the learn-ahead window, so it would come straight back
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)
        lines = static_lines(app.screen, "#summary")
        assert any("2 cards reviewed" in line for line in lines)
        assert any("1 answered correctly" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        sessions = {s for _, s in _reviews(built)}
        assert len(sessions) == 1

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)

    _drive(built, size, script)


def test_a_grade_key_before_the_reveal_is_typed_not_graded(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.press("2")
        await pilot.pause()
        assert _reviews(built) == []
        assert app.screen.query_one("#sf0", Input).value == "2"

    _drive(built, (40, 30), script)


def test_every_study_button_ignores_a_tap_right_after_it_appears(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(built, ("meaning_de_en",))
    monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 60.0)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        app.screen.query_one("#sf0", Input).value = "dog"
        await pilot.click("#reveal")
        await pilot.pause()
        assert app.screen.query_one("#fields").display
        assert _reviews(built) == []
        monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 0.0)
        await asyncio.sleep(0.3)
        await pilot.click("#reveal")
        await pilot.pause()
        assert not app.screen.query_one("#fields").display
        monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 60.0)
        await pilot.click("#grade2")
        await pilot.pause()
        assert _reviews(built) == []
        monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 0.0)
        await asyncio.sleep(0.3)
        await pilot.click("#grade2")
        await pilot.pause()
        assert [r for r, _ in _reviews(built)] == [3]

    _drive(built, (40, 30), script)


def test_escape_ends_the_session_with_a_summary(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)
        assert any("0 cards reviewed" in line for line in static_lines(app.screen, "#summary"))

    _drive(built, (40, 30), script)


def test_no_cards_goes_straight_to_the_summary(built: Workspace) -> None:
    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)

    _drive(built, (40, 30), script)


def test_a_learning_db_from_a_newer_harald_is_refused_with_a_message(built: Workspace) -> None:
    with sqlite3.connect(built.config.learning_db) as db:
        db.execute("CREATE TABLE alembic_version (version_num TEXT)")
        db.execute("INSERT INTO alembic_version VALUES ('9999')")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)
        assert any("does not know" in n.message for n in app._notifications)

    _drive(built, (40, 30), script)


def _answers(ws: Workspace) -> list[tuple[int, str]]:
    with sqlite3.connect(ws.config.learning_db) as db:
        return db.execute("SELECT rating, answer FROM review ORDER BY id").fetchall()


def _seed_verb(ws: Workspace, lemma: str = "anrufen") -> None:
    verb = LoadHeadword(ws.config).execute(lemma, "verb").unwrap().unwrap()
    plan = PlanWordCards(ws.config).execute(verb, 0, [0], []).unwrap()
    plan = CardPlan(
        plan.word_hint, tuple(c for c in plan.cards if c.card_type == "stammformen"), ()
    )
    CreateWordCards(ws.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()


async def _type_fields(app: HaraldApp, pilot: Pilot[None], *forms: str) -> None:
    for form in forms:
        for ch in form:
            await pilot.press("space" if ch == " " else ch)
        await pilot.press("enter")
    await pilot.pause()


def test_stammformen_next_button_ignores_a_tap_right_after_it_appears(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 1.0)
    _seed_verb(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _type_fields(app, pilot, "ruft an", "rief an", "hat angerufen")
        assert len(_reviews(built)) == 1
        await pilot.click("#cont")
        await pilot.pause()
        assert app.screen.query_one("#cont", Button).display
        await asyncio.sleep(1.05)
        await pilot.click("#cont")
        await pilot.pause()
        assert not app.screen.query_one("#cont", Button).display

    _drive(built, (40, 30), script)


@pytest.mark.parametrize("size", SIZES)
def test_stammformen_card_is_typed_and_graded_good_when_right(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_verb(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("Stammformen" in line for line in lines)
        assert any("anrufen  -  to call; to phone" in line for line in lines)
        assert not any("TRENNBAR" in line or "split forms" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert not app.screen.query_one("#reveal", Button).display
        assert app.screen.query_one("#fields").display
        assert_inside(app.screen, size)

        await pilot.press("space", "3")
        await pilot.pause()
        assert app.screen.query_one("#sf0", Input).value == " 3"
        app.screen.query_one("#sf0", Input).value = ""

        await _type_fields(app, pilot, "ruft an", "rief an", "hat angerufen")
        assert _answers(built) == [(3, "ruft an | rief an | hat angerufen")]
        lines = static_lines(app.screen, "#card")
        assert any(line.startswith("er/sie/es") and line.rstrip().endswith("ok") for line in lines)
        assert any("RIGHT - graded Good" in line for line in lines)
        assert any("trennbar: the prefix an" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert not app.screen.query_one("#fields").display
        assert app.screen.query_one("#cont", Button).display
        assert_inside(app.screen, size)

        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.query_one("#fields").display or isinstance(app.screen, SummaryScreen)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_wrong_stammformen_field_is_shown_in_place_and_graded_again(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_verb(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _type_fields(app, pilot, "ruft an", "rief", "")
        assert [r for r, _ in _answers(built)] == [1]
        lines = static_lines(app.screen, "#card")
        assert any(line.rstrip().endswith("WRONG") and "rief" in line for line in lines)
        assert any("-> rief an" in line for line in lines)
        assert any("(empty)" in line for line in lines)
        assert any("-> hat angerufen" in line for line in lines)
        assert any("WRONG - graded Again" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


def test_umlaut_digraphs_are_accepted_for_a_typed_form(built: Workspace) -> None:
    _seed_verb(built, "laufen")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _type_fields(app, pilot, "laeuft", "lief", "ist gelaufen")
        assert [r for r, _ in _answers(built)] == [3]

    _drive(built, (40, 30), script)


def _seed_conjugation(ws: Workspace, lemma: str, slot: str) -> None:
    verb = LoadHeadword(ws.config).execute(lemma, "verb").unwrap().unwrap()
    plan = PlanWordCards(ws.config).execute(verb, 0, [], [], [slot.rsplit(".", 1)[0]]).unwrap()
    plan = CardPlan(plan.word_hint, tuple(c for c in plan.cards if c.content["slot"] == slot), ())
    CreateWordCards(ws.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()


@pytest.mark.parametrize("size", SIZES)
def test_conjugation_card_shows_tense_and_person_and_grades_good_when_right(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_conjugation(built, "anrufen", "ind.pres.1sg")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("Conjugation" in line for line in lines)
        assert any("anrufen  -  to call; to phone" in line for line in lines)
        assert any("Präsens" in line for line in lines)
        assert not any("TRENNBAR" in line or "split" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert str(app.screen.query_one("#lbl0").render()).strip() == "ich"
        assert app.screen.query_one("#row0").display
        assert not app.screen.query_one("#row1").display
        assert not app.screen.query_one("#reveal", Button).display
        assert_inside(app.screen, size)

        await _type_fields(app, pilot, "rufe an")
        assert _answers(built) == [(3, "rufe an")]
        lines = static_lines(app.screen, "#card")
        assert any(line.startswith("ich") and line.rstrip().endswith("ok") for line in lines)
        assert any("RIGHT - graded Good" in line for line in lines)
        assert not any("trennbar" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert not app.screen.query_one("#fields").display
        assert app.screen.query_one("#cont", Button).display
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_wrong_conjugation_answer_is_graded_again_with_the_separable_note(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_conjugation(built, "anrufen", "ind.pres.1sg")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _type_fields(app, pilot, "rufe")
        assert _answers(built) == [(1, "rufe")]
        lines = static_lines(app.screen, "#card")
        assert any(line.rstrip().endswith("WRONG") and "rufe" in line for line in lines)
        assert any("-> rufe an" in line for line in lines)
        assert any("WRONG - graded Again" in line for line in lines)
        assert any("trennbar: the prefix an" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


def test_a_wrong_compound_conjugation_answer_shows_no_separable_note(built: Workspace) -> None:
    _seed_conjugation(built, "anrufen", "ind.perf.1sg")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("Perfekt" in line for line in lines)
        await _type_fields(app, pilot, "habe")
        lines = static_lines(app.screen, "#card")
        assert any("-> habe angerufen" in line for line in lines)
        assert any("WRONG - graded Again" in line for line in lines)
        assert not any("trennbar" in line for line in lines)

    _drive(built, (40, 30), script)


def test_a_conjugation_digraph_is_accepted(built: Workspace) -> None:
    _seed_conjugation(built, "laufen", "ind.pres.2sg")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _type_fields(app, pilot, "laeufst")
        assert [r for r, _ in _answers(built)] == [3]

    _drive(built, (40, 30), script)


def _seed_de_de(ws: Workspace, lemma: str = "Fernweh", entry: int | None = None) -> str:
    word = LoadHeadword(ws.config).execute(lemma, "noun").unwrap().unwrap()
    plan = PlanWordCards(ws.config).execute(word, entry, [], [(0, 0)]).unwrap()
    plan = CardPlan(
        plan.word_hint,
        tuple(c for c in plan.cards if c.card_type == "meaning_de_de"),
        plan.refusals,
    )
    CreateWordCards(ws.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()
    return str(plan.cards[0].content["definition"])


@pytest.mark.parametrize("size", SIZES)
def test_checked_german_german_front_shows_definition_pos_and_the_check_button(
    built: Workspace, size: tuple[int, int]
) -> None:
    definition = _seed_de_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, StudyScreen)
        lines = static_lines(app.screen, "#card")
        assert any("German -> German" in line for line in lines)
        assert any(definition.split()[0] in line for line in lines)
        assert any(line.strip() == "noun" for line in lines)
        assert not any("Fernweh" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert str(app.screen.query_one("#lbl0").render()).strip() == "Art. + noun"
        check = app.screen.query_one("#check", Button)
        assert check.display and str(check.label) == "Check (enter)"
        assert not app.screen.query_one("#reveal", Button).display
        assert app.screen.query_one("#digraphs").display
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_right_german_german_answer_is_graded_good_and_shows_the_expected_word(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_de_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "das Fernweh")
        assert _answers(built) == [(3, "das Fernweh")]
        lines = static_lines(app.screen, "#card")
        assert any("RIGHT - graded Good" in line for line in lines)
        you = next(i for i, line in enumerate(lines) if "you: das Fernweh" in line)
        assert lines[you + 1].strip() == "das Fernweh"
        assert all(len(line) <= size[0] for line in lines)
        assert app.screen.query_one("#cont", Button).display
        assert not app.screen.query_one("#fields").display
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize(
    ("typed", "rating", "verdict"),
    [
        ("der Fernweh", 2, "RIGHT, wrong article - graded Hard"),
        ("Fernweh", 2, "RIGHT, no article - graded Hard"),
        ("Xyz", 1, "WRONG - graded Again"),
        ("", 1, "No answer - graded Again"),
    ],
)
def test_german_german_hard_and_again_show_the_expected_word(
    built: Workspace, size: tuple[int, int], typed: str, rating: int, verdict: str
) -> None:
    _seed_de_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, typed)
        assert [r for r, _ in _answers(built)] == [rating]
        lines = static_lines(app.screen, "#card")
        assert any(verdict in line for line in lines)
        you = next(i for i, line in enumerate(lines) if "you:" in line)
        assert lines[you + 1].strip() == "das Fernweh"
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_german_german_retry_shows_the_cue_and_a_right_second_try_is_hard(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_de_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "das Hund")
        assert _reviews(built) == []
        assert _cue(app) == "Another noun. Try: F _ _ _ _ _ _"
        assert app.screen.query_one("#sf0", Input).has_focus
        assert_inside(app.screen, size)
        await asyncio.sleep(0.35)
        await _check(pilot, "das Fernweh")
        assert _answers(built) == [(2, "das Hund | das Fernweh")]
        lines = static_lines(app.screen, "#card")
        assert any("RIGHT on the second try - graded Hard" in line for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


def test_a_german_german_card_without_stored_labels_or_gender_still_checks(
    built: Workspace,
) -> None:
    _seed_de_de(built)
    _edit_card(built, labels=_GONE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "das Fernweh")
        assert _answers(built) == [(3, "das Fernweh")]

    _drive(built, (40, 30), script)


def test_a_band_card_expects_the_article_of_its_german_entry(built: Workspace) -> None:
    word = LoadHeadword(built.config).execute("Band", "noun").unwrap().unwrap()
    plan = PlanWordCards(built.config).execute(word, 0, [0], [(2, 0)]).unwrap()
    plan = CardPlan(
        plan.word_hint, tuple(c for c in plan.cards if c.card_type == "meaning_de_de"), ()
    )
    CreateWordCards(built.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "das Band")
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        assert any("RIGHT, wrong article - graded Hard" in line for line in lines)
        assert "der Band" in lines

    _drive(built, (40, 30), script)


def test_a_checked_german_german_card_fits_the_ten_rows_of_a_40x12_screen(
    built: Workspace,
) -> None:
    _seed_de_de(built)
    used: dict[str, int] = {}

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        body = app.screen.query_one("#body")
        used["front"] = _content_rows(body)
        await _check(pilot, "das Hund")
        used["retry"] = _content_rows(body)
        assert_inside(app.screen, (40, 12))
        await asyncio.sleep(0.35)
        await _check(pilot, "das Fernweh")
        used["verdict"] = _content_rows(body)
        assert_inside(app.screen, (40, 12))

    _drive(built, (40, 12), script)
    assert (used["front"], used["retry"], used["verdict"]) == (6, 5, 7)


def test_a_failed_write_on_an_empty_attempt_leaves_the_front_showing(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(built)

    class Failing:
        def __init__(self, config: object) -> None: ...

        def execute(self, *args: object, **kwargs: object) -> Result[None, StorageError]:
            return Result.err(StorageError("disk full"))

    monkeypatch.setattr("harald.tui.study.Grade", Failing)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert not any("you:" in line for line in static_lines(app.screen, "#card"))
        assert app.screen.query_one("#fields").display
        assert app.screen.query_one("#reveal", Button).display
        assert app.screen.check_action("reveal", ())

    _drive(built, (40, 30), script)


def test_a_graded_card_refits_when_the_terminal_gets_shorter(built: Workspace) -> None:
    _seed_verb(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _type_fields(app, pilot, "ruft an", "rief", "")
        await pilot.resize_terminal(40, 12)
        await pilot.pause()
        assert_inside(app.screen, (40, 12))

    _drive(built, (40, 30), script)


@pytest.mark.parametrize("size", SIZES)
def test_typed_cards_hint_at_the_digraphs_until_they_are_checked(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_verb(built)
    _seed_conjugation(built, "anrufen", "ind.pres.1sg")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        for answers in (("ruft an", "rief an", "hat angerufen"), ("rufe an",)):
            hint = static_lines(app.screen, "#digraphs")
            assert any("ae/oe/ue/ss are accepted for ä/ö/ü/ß" in line for line in hint)
            assert all(len(line) <= size[0] for line in hint)
            assert_inside(app.screen, size)
            await _type_fields(app, pilot, *answers)
            assert not app.screen.query_one("#digraphs").display
            await pilot.press("enter")
            await pilot.pause()

    _drive(built, size, script)


def test_a_meaning_card_does_not_mention_the_digraphs(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert not app.screen.query_one("#digraphs").display

    _drive(built, (40, 30), script)


def _edit_card(ws: Workspace, **changes: object) -> None:
    with sqlite3.connect(ws.config.learning_db) as db:
        for card_id, raw in db.execute("SELECT id, content FROM card").fetchall():
            content = json.loads(raw)
            for key, value in changes.items():
                if value is _GONE:
                    content.pop(key, None)
                else:
                    content[key] = value
            db.execute("UPDATE card SET content = ? WHERE id = ?", (json.dumps(content), card_id))


_GONE = object()


def _seed_en_de(ws: Workspace, **changes: object) -> None:
    _seed(ws, ("meaning_en_de",))
    _edit_card(ws, **changes)


async def _check(pilot: Pilot[None], typed: str) -> None:
    for ch in typed:
        await pilot.press("space" if ch == " " else ch)
    await pilot.press("enter")
    await pilot.pause()


@pytest.mark.parametrize("size", SIZES)
def test_checked_english_german_front_shows_gloss_pos_and_the_check_button(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built, labels=["derogatory"])

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("English -> German" in line for line in lines)
        assert any("[derogatory] dog (Canis familiaris)" in line.strip() for line in lines)
        assert any(line.strip() == "noun" for line in lines)
        assert any("The dog barks." in line for line in lines)
        assert not any("Hund" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert str(app.screen.query_one("#lbl0").render()).strip() == "Art. + noun"
        check = app.screen.query_one("#check", Button)
        assert check.display and str(check.label) == "Check (enter)"
        assert not app.screen.query_one("#reveal", Button).display
        assert app.screen.query_one("#digraphs").display
        hint = static_lines(app.screen, "#digraphs")
        assert any("ae/oe/ue/ss are accepted for ä/ö/ü/ß" in line for line in hint)
        assert_inside(app.screen, size)

    _drive(built, size, script)


def test_a_card_without_labels_or_pos_still_renders(built: Workspace) -> None:
    _seed_en_de(built, labels=_GONE, pos=_GONE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("dog (Canis familiaris)" in line for line in lines)
        assert not any("[" in line for line in lines)
        assert_inside(app.screen, (40, 30))

    _drive(built, (40, 30), script)


@pytest.mark.parametrize(
    ("changes", "label"),
    [
        ({}, "Art. + noun"),
        ({"gender": ""}, "Word"),
        ({"pos": "name"}, "Word"),
        ({"pos": "verb", "gender": ""}, "Word"),
    ],
)
def test_the_field_is_labelled_for_what_is_typed(
    built: Workspace, changes: dict[str, object], label: str
) -> None:
    _seed_en_de(built, **changes)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert str(app.screen.query_one("#lbl0").render()).strip() == label

    _drive(built, (40, 30), script)


@pytest.mark.parametrize("size", SIZES)
def test_a_right_checked_answer_is_graded_good_and_shows_the_expected_word(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "der Hund")
        assert _answers(built) == [(3, "der Hund")]
        lines = static_lines(app.screen, "#card")
        assert any("RIGHT - graded Good" in line for line in lines)
        you = next(i for i, line in enumerate(lines) if "you: der Hund" in line)
        assert lines[you + 1].strip() == "der Hund"
        assert any("Der Hund bellt." in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert app.screen.query_one("#cont", Button).display
        assert not app.screen.query_one("#check", Button).display
        assert not app.screen.query_one("#fields").display
        assert not app.screen.query_one("#digraphs").display
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize(
    ("typed", "rating", "verdict"),
    [
        ("die Hund", 2, "RIGHT, wrong article - graded Hard"),
        ("Hund", 2, "RIGHT, no article - graded Hard"),
        ("Xyz", 1, "WRONG - graded Again"),
        ("", 1, "No answer - graded Again"),
    ],
)
def test_hard_and_again_are_shown_with_the_expected_word(
    built: Workspace, size: tuple[int, int], typed: str, rating: int, verdict: str
) -> None:
    _seed_en_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        if typed:
            await _check(pilot, typed)
        else:
            await pilot.press("enter")
            await pilot.pause()
        assert [r for r, _ in _answers(built)] == [rating]
        lines = static_lines(app.screen, "#card")
        assert any(verdict in line for line in lines)
        you = next(i for i, line in enumerate(lines) if "you:" in line)
        assert lines[you + 1].strip() == "der Hund"
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, SummaryScreen) or rating

    _drive(built, size, script)


def test_a_second_wrong_article_is_graded_again(built: Workspace) -> None:
    _seed_en_de(built)
    card = NextCard(built.config).execute(datetime(2026, 1, 1, tzinfo=UTC)).unwrap().unwrap()
    Grade(built.config).execute(card.id, 1, datetime.now(UTC), "s0", None, "die Hund").unwrap()

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "das Hund")
        assert _answers(built)[-1][0] == 1
        lines = static_lines(app.screen, "#card")
        assert any("Wrong article twice - graded Again" in line for line in lines)

    _drive(built, (40, 30), script)


@pytest.mark.parametrize("size", SIZES)
def test_an_article_on_a_noun_with_no_gender_is_refused_without_a_grade(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built, gender="")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "die Hund")
        assert _reviews(built) == []
        assert app.screen.query_one("#sf0", Input).value == "die Hund"
        assert app.screen.focused is app.screen.query_one("#sf0", Input)
        hint = static_lines(app.screen, "#digraphs")
        assert " ".join(line.strip() for line in hint) == (
            "No article stored - type the word alone"
        )
        assert app.screen.query_one("#check", Button).display
        assert not any("you:" in line for line in static_lines(app.screen, "#card"))
        assert_inside(app.screen, size)

        app.screen.query_one("#sf0", Input).value = "Hund"
        await pilot.press("enter")
        await pilot.pause()
        assert _answers(built) == [(3, "Hund")]

    _drive(built, size, script)


def test_check_button_checks_and_ignores_a_tap_right_after_it_appears(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_en_de(built)
    monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 60.0)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        app.screen.query_one("#sf0", Input).value = "der Hund"
        await pilot.click("#check")
        await pilot.pause()
        assert _reviews(built) == []
        monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 0.0)
        await asyncio.sleep(0.3)
        await pilot.click("#check")
        await pilot.pause()
        assert _answers(built) == [(3, "der Hund")]

    _drive(built, (40, 30), script)


def test_study_returns_home_with_a_message_when_the_lexicon_has_gone(built: Workspace) -> None:
    _seed_en_de(built)
    built.config.lexicon.unlink()

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)
        assert any("Checking answers needs lexicon.db:" in n.message for n in app._notifications)
        assert _reviews(built) == []

    _drive(built, (40, 30), script)


def _cue(app: HaraldApp) -> str:
    return " ".join(line.strip() for line in static_lines(app.screen, "#digraphs"))


@pytest.mark.parametrize("size", SIZES)
def test_another_noun_asks_for_one_more_try_with_a_cue_and_grades_nothing(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "die Katze")
        assert _reviews(built) == []
        assert _cue(app) == "Another noun. Try: H _ _ _"
        field = app.screen.query_one("#sf0", Input)
        assert field.value == "" and field.has_focus
        assert app.screen.query_one("#check", Button).display
        assert not app.screen.query_one("#cont", Button).display
        lines = static_lines(app.screen, "#card")
        assert not any("you:" in line or "graded" in line for line in lines)
        assert not any("Hund" in line for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_long_word_cue_gives_the_first_letter_and_length_when_the_blanks_do_not_fit(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built, lemma="Aufenthaltsgenehmigung")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "Katze")
        if size[0] == 40:
            assert _cue(app) == "Another noun. Try: A... (22 letters)"
            assert len(static_lines(app.screen, "#digraphs")) == 1
        else:
            assert _cue(app) == "Another noun. Try: A " + " ".join("_" * 21)
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize(
    ("changes", "typed", "shown"),
    [
        ({"lemma": "Katze", "gender": "f"}, "die Ktaze", "die Katze"),
        ({"lemma": "Katze", "gender": "f"}, "die katze", "die Katze"),
    ],
)
def test_a_slip_passes_as_good_and_shows_the_corrected_spelling(
    built: Workspace,
    size: tuple[int, int],
    changes: dict[str, object],
    typed: str,
    shown: str,
) -> None:
    _seed_en_de(built, **changes)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, typed)
        assert _answers(built) == [(3, typed)]
        lines = static_lines(app.screen, "#card")
        assert any("RIGHT, typo - graded Good" in line for line in lines)
        you = next(i for i, line in enumerate(lines) if f"you: {typed}" in line)
        assert lines[you + 1].strip() == shown
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_capitalisation_slip_that_spells_another_word_is_graded_again(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built, lemma="Essen", gender="n")

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "das essen")
        assert _answers(built) == [(1, "das essen")]
        lines = static_lines(app.screen, "#card")
        assert any("WRONG, capitalisation - graded Again" in line for line in lines)
        you = next(i for i, line in enumerate(lines) if "you: das essen" in line)
        assert lines[you + 1].strip() == "das Essen"
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize(
    ("second", "rating", "verdict"),
    [
        ("der Hund", 2, "RIGHT on the second try - graded Hard"),
        ("Hund", 2, "RIGHT on the second try - graded Hard"),
        ("die Katze", 1, "WRONG - graded Again"),
        ("Xyz", 1, "WRONG - graded Again"),
        ("", 1, "No answer - graded Again"),
    ],
)
def test_the_second_try_is_graded_hard_when_right_and_again_otherwise(
    built: Workspace, size: tuple[int, int], second: str, rating: int, verdict: str
) -> None:
    _seed_en_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "die Katze")
        await asyncio.sleep(0.35)
        await _check(pilot, second)
        assert _answers(built) == [(rating, f"die Katze | {second}")]
        lines = static_lines(app.screen, "#card")
        assert any(verdict in line for line in lines)
        you = next(i for i, line in enumerate(lines) if "you:" in line)
        assert lines[you + 1].strip() == "der Hund"
        assert_inside(app.screen, size)
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.query_one("#sf0", Input).value == ""
        assert "Try" not in _cue(app)

    _drive(built, size, script)


def test_the_retry_survives_a_resize_and_the_next_card_starts_fresh(built: Workspace) -> None:
    _seed_en_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "die Katze")
        for size in ((40, 12), (100, 30), (40, 30)):
            await pilot.resize_terminal(*size)
            await pilot.pause()
            assert _cue(app) == "Another noun. Try: H _ _ _"
            assert app.screen.query_one("#sf0", Input).has_focus
            assert_inside(app.screen, size)
        await _check(pilot, "Hund")
        assert _answers(built) == [(2, "die Katze | Hund")]

    _drive(built, (40, 30), script)


def test_the_retry_cue_fits_the_ten_rows_of_a_40x12_screen(built: Workspace) -> None:
    _seed_en_de(built)
    used: dict[str, int] = {}

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        body = app.screen.query_one("#body")
        used["front"] = _content_rows(body)
        await _check(pilot, "die Katze")
        used["retry"] = _content_rows(body)
        assert_inside(app.screen, (40, 12))
        await asyncio.sleep(0.35)
        await _check(pilot, "der Hund")
        used["verdict"] = _content_rows(body)
        assert_inside(app.screen, (40, 12))

    _drive(built, (40, 12), script)
    assert (used["retry"], used["verdict"]) == (6, 9)


def test_the_retry_reuses_the_check_button_and_its_tap_guard(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_en_de(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "die Katze")
        monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 60.0)
        await pilot.click("#check")
        await pilot.pause()
        assert _reviews(built) == []
        monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 0.0)
        await asyncio.sleep(0.3)
        await pilot.click("#check")
        await pilot.pause()
        assert _answers(built) == [(1, "die Katze | ")]

    _drive(built, (40, 30), script)


def _content_rows(body: Widget) -> int:
    return sum(child.outer_size.height for child in body.children if child.display)


_SHORT_EXAMPLE = {"text": "Der Hund bellt.", "translation": "The dog barks."}
_NOTE = "the animal, not the slang"
_LONG_EXAMPLE = {
    "text": "Der Hund bellt jeden Morgen so laut, dass die ganze Nachbarschaft davon wach wird.",
    "translation": "The dog barks so loudly every morning that the whole neighbourhood wakes up.",
}


def _note_rows(lines: list[str]) -> list[int]:
    return [i for i, line in enumerate(lines) if f"({_NOTE})" in line]


def _without_note(lines: list[str]) -> list[str]:
    return [line for line in lines if f"({_NOTE})" not in line]


@pytest.mark.parametrize("size", SIZES)
def test_a_note_sits_under_the_pos_and_above_the_example_on_a_german_english_front(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed(built, ("meaning_de_en",))
    _edit_card(built, note=_NOTE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        [at] = _note_rows(lines)
        assert lines[at - 1] == "noun"
        assert "Der Hund bellt." in lines[at + 1 :]
        assert max(len(line) for line in lines) <= size[0]
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_note_sits_under_the_pos_and_above_the_example_on_an_english_german_front(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built, note=_NOTE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        [at] = _note_rows(lines)
        assert lines[at - 1] == "noun"
        assert "The dog barks." in lines[at + 1 :]
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_the_german_english_front_with_a_note_and_a_three_row_example_fits(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed(built, ("meaning_de_en",))
    _edit_card(built, note=_NOTE, example=_LONG_EXAMPLE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert len(_note_rows([line.strip() for line in lines])) == 1
        assert any("Nachbarschaft" in line for line in lines)
        assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_the_note_stays_after_the_reveal(built: Workspace, size: tuple[int, int]) -> None:
    _seed(built, ("meaning_de_en",))
    _edit_card(built, note=_NOTE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await pilot.press(*"dog", "enter")
        await pilot.pause()
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        [at] = _note_rows(lines)
        assert lines[at - 1] == "noun"
        assert lines.index("you: dog") > at
        assert max(len(line) for line in lines) <= size[0]
        if size[1] > 12:
            assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_a_card_without_a_note_renders_as_before(built: Workspace, size: tuple[int, int]) -> None:
    _seed(built, ("meaning_de_en",))
    seen: dict[str, list[str]] = {}

    async def front_and_back(app: HaraldApp, pilot: Pilot[None], key: str) -> None:
        await pilot.press("s")
        await pilot.pause()
        front = static_lines(app.screen, "#card")
        await pilot.press(*"dog", "enter")
        await pilot.pause()
        seen[key] = [*front, "", *static_lines(app.screen, "#card")]

    async def plain(app: HaraldApp, pilot: Pilot[None]) -> None:
        await front_and_back(app, pilot, "plain")

    _drive(built, size, plain)
    _edit_card(built, note=_NOTE)

    async def noted(app: HaraldApp, pilot: Pilot[None]) -> None:
        await front_and_back(app, pilot, "noted")

    _drive(built, size, noted)
    assert len(seen["noted"]) == len(seen["plain"]) + 2
    assert _without_note(seen["noted"]) == seen["plain"]


@pytest.mark.parametrize("size", SIZES)
def test_both_cards_of_a_sense_carry_its_note(built: Workspace, size: tuple[int, int]) -> None:
    hund = LoadHeadword(built.config).execute("Hund", "noun").unwrap().unwrap()
    plan = PlanWordCards(built.config).execute(hund, 0, [0], [], [], {0: _NOTE}).unwrap()
    CreateWordCards(built.config).execute(plan, datetime(2026, 1, 1, tzinfo=UTC)).unwrap()
    headings: list[str] = []

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        for _ in range(2):
            lines = static_lines(app.screen, "#card")
            headings.append(lines[0].strip())
            assert len(_note_rows([line.strip() for line in lines])) == 1
            await pilot.press("enter")
            await pilot.pause()
            await asyncio.sleep(0.35)
            await pilot.press("enter")
            await pilot.pause()

    _drive(built, size, script)
    assert sorted(headings) == ["English -> German", "German -> English"]


@pytest.mark.parametrize("size", SIZES)
def test_a_german_german_card_carries_its_note(built: Workspace, size: tuple[int, int]) -> None:
    _seed_de_de(built)
    _edit_card(built, note=_NOTE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        [at] = _note_rows(lines)
        assert lines[at - 1] == "noun"
        assert_inside(app.screen, size)
        await _check(pilot, "das Fernweh")
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        assert len(_note_rows(lines)) == 1
        if size[1] > 12:
            assert_inside(app.screen, size)

    _drive(built, size, script)


@pytest.mark.parametrize("size", SIZES)
def test_the_note_stays_through_a_retry_and_the_verdict(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed_en_de(built, note=_NOTE)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await _check(pilot, "die Katze")
        assert _cue(app) == "Another noun. Try: H _ _ _"
        assert len(_note_rows([line.strip() for line in static_lines(app.screen, "#card")])) == 1
        assert_inside(app.screen, size)
        await asyncio.sleep(0.35)
        await _check(pilot, "der Hund")
        assert len(_note_rows([line.strip() for line in static_lines(app.screen, "#card")])) == 1
        if size[1] > 12:
            assert_inside(app.screen, size)

    _drive(built, size, script)


def test_a_note_longer_than_a_row_is_cut_to_one_row(built: Workspace) -> None:
    _seed(built, ("meaning_de_en",))
    _edit_card(built, note="x" * 80)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = [line.strip() for line in static_lines(app.screen, "#card")]
        [cut] = [line for line in lines if line.startswith("(x")]
        assert cut.endswith("...)") and len(cut) <= 38
        assert_inside(app.screen, (40, 30))

    _drive(built, (40, 30), script)


def test_a_36_character_note_fits_a_40_column_row_whole(built: Workspace) -> None:
    note = "n" * 36
    _seed(built, ("meaning_de_en",))
    _edit_card(built, note=note)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        for size in ((40, 30), (40, 12)):
            await pilot.resize_terminal(*size)
            await pilot.pause()
            assert f"({note})" in [line.strip() for line in static_lines(app.screen, "#card")]

    _drive(built, (40, 30), script)


def test_note_on_german_english_after_reveal_at_40x12(built: Workspace) -> None:
    """D42/P64: the overflow in rows after the reveal, with and without a note.

    It does not use assert_inside: that fails on vertical scrolling, which is the
    thing measured here and which the design accepts. Only the difference is asserted.
    """
    _seed(built, ("meaning_de_en",))
    measured: dict[tuple[str, str], tuple[int, int, int]] = {}
    run: dict[str, tuple[int, int, int]] = {}

    async def reveal(app: HaraldApp, pilot: Pilot[None]) -> tuple[int, int, int]:
        await pilot.press("s")
        await pilot.pause()
        await pilot.press(*"dog", "enter")
        await pilot.pause()
        body = app.screen.query_one("#body")
        return body.max_scroll_y, _content_rows(body), body.size.height

    for example, content in (("short", None), ("three rows", _LONG_EXAMPLE)):
        for noted in (False, True):
            _edit_card(built, note=_NOTE if noted else _GONE, example=content or _SHORT_EXAMPLE)

            async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
                run["rows"] = await reveal(app, pilot)

            _drive(built, (40, 12), script)
            measured["with" if noted else "without", example] = run["rows"]

    print(f"(max_scroll_y, rows used, body height): {measured}")
    for example in ("short", "three rows"):
        with_note, without = measured["with", example], measured["without", example]
        assert with_note[1] - without[1] == 1, (example, with_note, without)
