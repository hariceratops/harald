import asyncio
import sqlite3
from datetime import UTC, datetime

import pytest
from textual.pilot import Pilot
from textual.widgets import Button, Input

from harald.learning.content import CardPlan
from harald.tui.app import HaraldApp
from harald.tui.home import HomeScreen
from harald.tui.study import StudyScreen, SummaryScreen
from harald.use_cases.cards import CreateWordCards, PlanWordCards
from harald.use_cases.lexicon import LoadHeadword
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
        assert not app.screen.query_one("#grade4", Button).display
        assert_inside(app.screen, size)

        await pilot.press("space")
        await pilot.pause()
        assert app.screen.query_one("#grade4", Button).display
        assert_inside(app.screen, size)
        await pilot.press("4")
        await pilot.pause()
        assert len(_reviews(built)) == 1

        await pilot.press("space")
        await pilot.press("4")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)
        lines = static_lines(app.screen, "#summary")
        assert any("2 cards reviewed" in line for line in lines)
        assert any("2 answered correctly" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert_inside(app.screen, size)
        sessions = {s for _, s in _reviews(built)}
        assert len(sessions) == 1

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)

    _drive(built, size, script)


def test_a_grade_before_the_reveal_is_ignored(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.press("3")
        await pilot.pause()
        assert _reviews(built) == []

    _drive(built, (40, 30), script)


def test_grade_buttons_ignore_a_tap_right_after_they_appear(built: Workspace) -> None:
    _seed(built)

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await pilot.click("#reveal")
        await pilot.pause()
        await pilot.click("#grade4")
        await pilot.pause()
        assert _reviews(built) == []
        await asyncio.sleep(0.35)
        await pilot.click("#grade4")
        await pilot.pause()
        assert [r for r, _ in _reviews(built)] == [4]

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


@pytest.mark.parametrize("size", SIZES)
def test_article_card_is_answered_with_one_key_and_shows_feedback(
    built: Workspace, size: tuple[int, int]
) -> None:
    _seed(built, ("article",))

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        lines = static_lines(app.screen, "#card")
        assert any("Article" in line for line in lines)
        assert any("Hund   (pl. Hunde)" in line for line in lines)
        assert any("dog (Canis familiaris)" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert not app.screen.query_one("#reveal", Button).display
        assert all(app.screen.query_one(f"#art{n}", Button).display for n in (1, 2, 3))
        assert not app.screen.query_one("#cont", Button).display
        assert_inside(app.screen, size)

        await pilot.press("space", "4")
        await pilot.pause()
        assert _reviews(built) == []

        await pilot.press("2")
        await pilot.pause()
        assert _answers(built) == [(1, "die")]
        lines = static_lines(app.screen, "#card")
        assert any("WRONG   der Hund" in line for line in lines)
        assert any("(you chose: die)" in line for line in lines)
        assert all(len(line) <= size[0] for line in lines)
        assert app.screen.query_one("#cont", Button).display
        assert not app.screen.query_one("#art1", Button).display
        assert_inside(app.screen, size)

        await pilot.press("1")
        await pilot.pause()
        assert len(_reviews(built)) == 1

        await pilot.press("enter")
        await pilot.pause()
        # the lapsed card is inside the learn-ahead window, so it comes straight back
        assert isinstance(app.screen, StudyScreen)
        assert not app.screen.query_one("#cont", Button).display
        assert app.screen.query_one("#art1", Button).display
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SummaryScreen)
        assert any("1 card reviewed" in x for x in static_lines(app.screen, "#summary"))
        assert any("0 answered correctly" in x for x in static_lines(app.screen, "#summary"))

    _drive(built, size, script)


def test_a_correct_article_is_good_and_space_continues(built: Workspace) -> None:
    _seed(built, ("article",))

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.press("1")
        await pilot.pause()
        assert _answers(built) == [(3, "der")]
        assert any("RIGHT   der Hund" in x for x in static_lines(app.screen, "#card"))
        await pilot.press("space")
        await pilot.pause()
        assert app.screen.query_one("#art1", Button).display
        assert not app.screen.query_one("#cont", Button).display

    _drive(built, (40, 30), script)


def test_article_buttons_answer_and_ignore_a_tap_right_after_they_appear(
    built: Workspace, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("harald.tui.study._TAP_GUARD_S", 1.0)
    _seed(built, ("article",))

    async def script(app: HaraldApp, pilot: Pilot[None]) -> None:
        await pilot.press("s")
        await pilot.pause()
        await pilot.click("#art1")
        await pilot.pause()
        assert _reviews(built) == []
        await asyncio.sleep(1.05)
        await pilot.click("#art1")
        await pilot.pause()
        assert _answers(built) == [(3, "der")]
        await pilot.click("#cont")
        await pilot.pause()
        assert app.screen.query_one("#cont", Button).display
        await asyncio.sleep(1.05)
        await pilot.click("#cont")
        await pilot.pause()
        assert not app.screen.query_one("#cont", Button).display

    _drive(built, (40, 30), script)


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
        assert any("TRENNBAR  an|rufen" in line for line in lines)
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
